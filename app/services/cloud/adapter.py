from abc import ABC, abstractmethod
from typing import TypedDict

from sqlalchemy.orm import Session

from app.domain.models.cloud_connection import CloudConnection


class UploadResult(TypedDict):
    id: str
    url: str | None

class CloudStorageAdapter(ABC):
    @abstractmethod
    def upload_file(self, file_path: str, connection: CloudConnection, db: Session) -> UploadResult:
        pass
