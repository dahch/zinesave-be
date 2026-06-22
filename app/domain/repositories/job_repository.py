from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.domain.models.job import Job
from app.domain.models.job_content import JobContent
from app.domain.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self, db: Session):
        super().__init__(Job, db)

    def get_user_job(self, job_id: str, user_id: int) -> Optional[Job]:
        return self.db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()

    def get_recent_duplicate(
        self, user_id: int, source_url: str, minutes: int = 10
    ) -> Optional[Job]:
        recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return (
            self.db.query(Job)
            .filter(
                Job.user_id == user_id,
                Job.source_url == source_url,
                Job.created_at > recent_cutoff,
                Job.status.in_(["queued", "processing"]),
            )
            .first()
        )

    def get_user_jobs_paginated(self, user_id: int, skip: int, limit: int) -> Tuple[List[Job], int]:
        query = self.db.query(Job).filter(Job.user_id == user_id)
        total = query.count()
        jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
        return jobs, total

    def get_recent_jobs(self, user_id: int, limit: int = 5) -> List[Job]:
        return (
            self.db.query(Job)
            .filter(Job.user_id == user_id)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .all()
        )

    def add_content(self, job_content: JobContent) -> JobContent:
        self.db.add(job_content)
        self.db.commit()
        self.db.refresh(job_content)
        return job_content
