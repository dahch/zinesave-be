from typing import Optional
from sqlalchemy.orm import Session
from app.domain.repositories.base import BaseRepository
from app.domain.models.cloud_connection import CloudConnection

class CloudConnectionRepository(BaseRepository[CloudConnection]):
    def __init__(self, db: Session):
        super().__init__(CloudConnection, db)

    def get_by_user_and_provider(self, user_id: int, provider: str) -> Optional[CloudConnection]:
        return self.db.query(CloudConnection).filter(
            CloudConnection.user_id == user_id,
            CloudConnection.provider == provider
        ).first()
