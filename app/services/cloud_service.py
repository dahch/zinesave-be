from sqlalchemy.orm import Session
from app.domain.models.cloud_connection import CloudConnection
from app.services.cloud.adapter import CloudStorageAdapter
from app.services.cloud.google_drive import GoogleDriveAdapter
from app.services.cloud.dropbox import DropboxAdapter
from app.services.cloud.onedrive import OneDriveAdapter

class CloudService:
    @staticmethod
    def get_adapter(provider: str) -> CloudStorageAdapter:
        if provider == "google_drive":
            return GoogleDriveAdapter()
        elif provider == "dropbox":
            return DropboxAdapter()
        elif provider == "onedrive":
            return OneDriveAdapter()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    @staticmethod
    def upload_file(db: Session, user_id: str, provider: str, file_path: str):
        adapter = CloudService.get_adapter(provider)
        
        connection = (
            db.query(CloudConnection)
            .filter(
                CloudConnection.user_id == user_id,
                CloudConnection.provider == provider
            )
            .first()
        )

        if not connection:
            raise ValueError(f"User is not connected to {provider}")

        return adapter.upload_file(file_path, connection, db)
