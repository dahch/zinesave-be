from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.models.job import Job


def count_active_jobs(db: Session, user_id: str):
    """Count jobs created in the last 30 days, excluding failed ones.

    This prevents users from being permanently locked out due to
    failed jobs counting against their quota.
    """
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    return (
        db.query(func.count(Job.id))
        .filter(Job.user_id == user_id, Job.status != "failed", Job.created_at > thirty_days_ago)
        .scalar()
    )


# Keep backward compat alias
count_jobs = count_active_jobs
