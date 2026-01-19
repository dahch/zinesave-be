from sqlalchemy.orm import Session
from sqlalchemy import func
from app.domain.models.job import Job

def count_jobs(db: Session, user_id: str):
    return (
        db.query(func.count(Job.id))
        .filter(
            Job.user_id == user_id
        )
        .scalar()
    )