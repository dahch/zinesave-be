from typing import Optional
from sqlalchemy.orm import Session
from app.domain.repositories.base import BaseRepository
from app.domain.models.file import File

class FileRepository(BaseRepository[File]):
    def __init__(self, db: Session):
        super().__init__(File, db)

    def get_epub_by_job_id(self, job_id: str) -> Optional[File]:
        return self.db.query(File).filter(
            File.job_id == job_id,
            File.type == "epub",
            File.is_deleted == False
        ).first()
