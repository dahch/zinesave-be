from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.models.cloud_connection import CloudConnection
from app.services.cloud.adapter import CloudStorageAdapter, UploadResult


class GoogleDriveAdapter(CloudStorageAdapter):
    def upload_file(self, file_path: str, connection: CloudConnection, db: Session) -> UploadResult:
        creds = Credentials(
            token=connection.access_token,
            refresh_token=connection.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Update connection in DB
            connection.access_token = creds.token
            if creds.expiry:
                connection.expires_at = creds.expiry
            db.commit()

        service = build("drive", "v3", credentials=creds)

        file_metadata = {"name": file_path.split("/")[-1], "mimeType": "application/epub+zip"}

        media = MediaFileUpload(file_path, mimetype="application/epub+zip", resumable=True)

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id, webViewLink")
            .execute()
        )

        return {"id": file.get("id"), "url": file.get("webViewLink")}
