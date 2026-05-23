import os
import json
import logging
import requests
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.domain.models.cloud_connection import CloudConnection
from app.services.cloud.adapter import CloudStorageAdapter, UploadResult

logger = logging.getLogger(__name__)

class DropboxAdapter(CloudStorageAdapter):
    def upload_file(self, file_path: str, connection: CloudConnection, db: Session) -> UploadResult:
        # 1. Refresh Token if needed
        self._refresh_token_if_needed(connection, db)

        # 2. Upload
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        headers = {
            "Authorization": f"Bearer {connection.access_token}",
            "Dropbox-API-Arg": json.dumps({
                "path": f"/{filename}",
                "mode": "add",
                "autorename": True,
                "mute": False
            }),
            "Content-Type": "application/octet-stream"
        }

        with open(file_path, "rb") as f:
            data = f.read()

        response = requests.post(
            "https://content.dropboxapi.com/2/files/upload",
            headers=headers,
            data=data
        )
        
        if response.status_code != 200:
             raise Exception(f"Dropbox upload failed: {response.text}")

        res_json = response.json()
        
        # 3. Create Shared Link (to get a URL)
        # We need a separate call to share the file and get user accessible URL
        link_url = self._create_shared_link(filename, connection.access_token)
        
        return {
            "id": res_json.get("id"),
            "url": link_url
        }

    def _create_shared_link(self, path: str, token: str) -> str:
        url = "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "path": f"/{path}"
        }
        
        resp = requests.post(url, headers=headers, json=data)
        
        # If create failed (e.g. already shared), try get existing
        if resp.status_code == 409:
             return self._get_existing_link(path, token)

        if resp.status_code != 200:
            logger.warning(f"Failed to create Dropbox shared link: {resp.status_code} {resp.text}")
            return None
            
        return resp.json().get("url")

    def _get_existing_link(self, path: str, token: str) -> str:
        url = "https://api.dropboxapi.com/2/sharing/list_shared_links"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        data = {"path": f"/{path}", "direct_only": True}
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 200:
            links = resp.json().get("links", [])
            if links:
                return links[0].get("url")
        return None

    def _refresh_token_if_needed(self, connection: CloudConnection, db: Session):
        """Refresh Dropbox access token using the refresh token.
        
        Dropbox short-lived tokens expire in ~4 hours. We proactively
        refresh if we detect the token might be expired (no expires_at set,
        or expires_at is in the past).
        """
        if not connection.refresh_token:
            logger.debug("No Dropbox refresh token available, skipping refresh")
            return
        
        # If we have an expires_at and it's still valid (with 5 min buffer), skip
        if connection.expires_at:
            if connection.expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
                return
        
        logger.info("Refreshing Dropbox access token")
        
        client_id = os.getenv("DROPBOX_CLIENT_ID")
        client_secret = os.getenv("DROPBOX_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            logger.error("DROPBOX_CLIENT_ID or DROPBOX_CLIENT_SECRET not set")
            return
        
        token_url = "https://api.dropbox.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": connection.refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        
        try:
            response = requests.post(token_url, data=data)
            if response.status_code != 200:
                logger.error(f"Dropbox token refresh failed: {response.status_code} {response.text}")
                return
            
            tokens = response.json()
            connection.access_token = tokens["access_token"]
            
            # Dropbox returns expires_in (seconds)
            expires_in = tokens.get("expires_in", 14400)  # Default 4h
            connection.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            db.commit()
            logger.info("Dropbox token refreshed successfully")
            
        except Exception as e:
            logger.error(f"Error refreshing Dropbox token: {e}")
