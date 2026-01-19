from sqlalchemy.orm import Session
from app.domain.models.job import Job
from app.services.extract_service import extract_content
import logging
import sentry_sdk
from app.services.normalize_service import normalize_html
from app.services.epub_service import generate_epub

logger = logging.getLogger(__name__)


def run_pipeline(job_id: str, db_factory):
    """
    db_factory: function that returns a new Session
    """
    db: Session = db_factory()

    try:
        logger.info(f"Pipeline looking for job {job_id}")
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.warning(f"Job {job_id} not found in DB")
            return
        
        logger.info(f"Job {job_id} found, setting status to processing")
        job.status = "processing"
        db.commit()

        #STEP 1 - Extract
        sentry_sdk.add_breadcrumb(category="pipeline", message="Starting extraction", level="info")
        extract_content(db, job)

        #STEP 2 - Normalize
        sentry_sdk.add_breadcrumb(category="pipeline", message="Starting normalization", level="info")
        normalize_html(db, job)

        #STEP 3 - Generate EPUB
        sentry_sdk.add_breadcrumb(category="pipeline", message="Starting EPUB generation", level="info")
        epub_path = generate_epub(db, job)

        #STEP 4 - Upload (NOW MANUAL via /jobs/{id}/upload)
        
        job.status = "done"
        job.current_step = None
        job.progress = 100
        db.commit()


    except Exception as e:
        logger.exception(f"Pipeline failed for job {job_id}")
        job.status = "failed"
        job.error_message = str(e)
        sentry_sdk.capture_exception(e)
        db.commit()

    finally:
        db.close()
