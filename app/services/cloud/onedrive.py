import logging
import os
from datetime import datetime, timedelta, timezone

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.models.cloud_connection import CloudConnection
from app.services.cloud.adapter import CloudStorageAdapter, UploadResult

logger = logging.getLogger(__name__)


class OneDriveAdapter(CloudStorageAdapter):
    def upload_file(self, file_path: str, connection: CloudConnection, db: Session) -> UploadResult:
        # 1. Refresh Token
        self._refresh_token_if_needed(connection, db)

        filename = os.path.basename(file_path)

        # 2. Upload to Root (PUT /me/drive/root:/{filename}:/content)
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{filename}:/content"

        with open(file_path, "rb") as f:
            data = f.read()

        headers = {
            "Authorization": f"Bearer {connection.access_token}",
            "Content-Type": "application/octet-stream",
        }

        response = requests.put(url, headers=headers, data=data)

        if response.status_code not in (200, 201):
            raise Exception(f"OneDrive upload failed: {response.text}")

        res_json = response.json()

        return {"id": res_json.get("id"), "url": res_json.get("webUrl")}

    def _refresh_token_if_needed(self, connection: CloudConnection, db: Session):
        """Refresh OneDrive/Microsoft Graph access token.

        Microsoft tokens expire in ~1 hour. We proactively refresh
        if expires_at is in the past or within 5 minutes.
        """
        if not connection.refresh_token:
            logger.debug("No OneDrive refresh token available, skipping refresh")
            return

        # If we have an expires_at and it's still valid (with 5 min buffer), skip
        if connection.expires_at:
            if connection.expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
                return

        logger.info("Refreshing OneDrive access token")

        client_id = settings.ONEDRIVE_CLIENT_ID
        client_secret = settings.ONEDRIVE_CLIENT_SECRET

        if not client_id or not client_secret:
            logger.error("ONEDRIVE_CLIENT_ID or ONEDRIVE_CLIENT_SECRET not set")
            return

        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            "client_id": client_id,
            "scope": "Files.ReadWrite User.Read offline_access",
            "refresh_token": connection.refresh_token,
            "redirect_uri": settings.BACKEND_URL + "/auth/onedrive/callback",
            "grant_type": "refresh_token",
            "client_secret": client_secret,
        }

        try:
            response = requests.post(token_url, data=data)
            if response.status_code != 200:
                logger.error(
                    f"OneDrive token refresh failed: {response.status_code} {response.text}"
                )
                return

            tokens = response.json()
            connection.access_token = tokens["access_token"]

            # Microsoft returns new refresh_token too
            if tokens.get("refresh_token"):
                connection.refresh_token = tokens["refresh_token"]

            # expires_in is in seconds (typically 3600 = 1h)
            expires_in = tokens.get("expires_in", 3600)
            connection.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            db.commit()
            logger.info("OneDrive token refreshed successfully")

        except Exception as e:
            logger.error(f"Error refreshing OneDrive token: {e}")
