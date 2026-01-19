from urllib.parse import urlparse

from sqlalchemy.orm import Session
from app.domain.models.job import Job
from app.domain.models.user import User

def create_job(db: Session, url: str, current_user: User) -> Job:
    parsed = urlparse(str(url))
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    job = Job(
        source_url=str(url),
        base_url=base_url,
        user_id=current_user.id
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job