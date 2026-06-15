from app.domain.models.cloud_connection import CloudConnection
from app.domain.repositories.cloud_connection_repository import CloudConnectionRepository
from app.services.cloud.adapter import CloudStorageAdapter
from app.services.cloud.dropbox import DropboxAdapter
from app.services.cloud.google_drive import GoogleDriveAdapter
from app.services.cloud.onedrive import OneDriveAdapter


class CloudService:
    def __init__(self, cloud_conn_repo: CloudConnectionRepository):
        self.cloud_conn_repo = cloud_conn_repo

    def get_adapter(self, provider: str) -> CloudStorageAdapter:
        if provider == "google_drive":
            return GoogleDriveAdapter()
        elif provider == "dropbox":
            return DropboxAdapter()
        elif provider == "onedrive":
            return OneDriveAdapter()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def upload_file(self, user_id: str, provider: str, file_path: str):
        adapter = self.get_adapter(provider)
        
        connection = self.cloud_conn_repo.get_by_user_and_provider(user_id, provider)

        if not connection:
            raise ValueError(f"User is not connected to {provider}")

        return adapter.upload_file(file_path, connection, self.cloud_conn_repo.db)
