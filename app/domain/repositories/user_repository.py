from typing import Optional
from sqlalchemy.orm import Session
from app.domain.repositories.base import BaseRepository
from app.domain.models.user import User

class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
        return self.db.query(User).filter(
            User.provider == provider,
            User.provider_id == provider_id
        ).first()
