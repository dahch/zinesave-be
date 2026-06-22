import json
import logging

import sentry_sdk
from sqlalchemy.orm import Session

from app.domain.models.job import Job
from app.domain.models.job_content import JobContent
from app.services.epub_service import generate_epub
from app.services.extract_service import extract_content, fetch_and_extract
from app.services.normalize_service import normalize_html, process_html_normalization

logger = logging.getLogger(__name__)


def run_composite_pipeline(job: Job, db: Session):
    sentry_sdk.add_breadcrumb(
        category="pipeline", message="Starting composite pipeline", level="info"
    )

    meta_content = (
        db.query(JobContent)
        .filter(JobContent.job_id == job.id, JobContent.step == "composite_meta")
        .first()
    )

    if not meta_content:
        raise Exception("Composite meta not found")

    data = json.loads(meta_content.content)
    urls = data.get("urls", [])
    title = data.get("title", "Composite EPUB")

    sources = []

    for i, url in enumerate(urls):
        logger.info(f"Composite job {job.id}: Processing part {i} ({url})")
        # Extract
        extract_result = fetch_and_extract(url)
        content_extracted = JobContent(
            job_id=job.id,
            step=f"extracted_{i}",
            content_type="html",
            content=extract_result["html"],
        )
        db.add(content_extracted)

        # Normalize
        norm_result = process_html_normalization(extract_result["html"])
        content_normalized = JobContent(
            job_id=job.id, step=f"normalized_{i}", content_type="html", content=norm_result["html"]
        )
        db.add(content_normalized)

        source = extract_result["metadata"].get("source", "Unknown")
        if source not in sources and source:
            sources.append(source)

    # Save combined metadata
    authors = ", ".join(sources)
    combined_meta = {
        "title": title,
        "author": authors,
        "publisher": "ReaderToEpub",
        "published": "",
        "source": authors,
        "language": "en",
        "url": urls[0] if urls else "",
    }

    meta_job_content = JobContent(
        job_id=job.id, step="metadata", content_type="json", content=json.dumps(combined_meta)
    )
    db.add(meta_job_content)

    db.commit()

    sentry_sdk.add_breadcrumb(
        category="pipeline", message="Starting composite EPUB generation", level="info"
    )
    epub_path = generate_epub(db, job)
    return epub_path


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

        if job.base_url == "composite":
            run_composite_pipeline(job, db)
        else:
            # STEP 1 - Extract
            sentry_sdk.add_breadcrumb(
                category="pipeline", message="Starting extraction", level="info"
            )
            extract_content(db, job)

            # STEP 2 - Normalize
            sentry_sdk.add_breadcrumb(
                category="pipeline", message="Starting normalization", level="info"
            )
            normalize_html(db, job)

            # STEP 3 - Generate EPUB
            sentry_sdk.add_breadcrumb(
                category="pipeline", message="Starting EPUB generation", level="info"
            )
            generate_epub(db, job)

        # STEP 4 - Upload (NOW MANUAL via /jobs/{id}/upload)

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
