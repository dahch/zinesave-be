import os
import asyncio
import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from arq import create_pool
from arq.cron import cron
from app.core.database import SessionLocal
from app.services.pipeline_service import run_pipeline
from app.core.queue import redis_settings
from app.services.retention_service import RetentionService

# Import models to ensure they are registered with SQLAlchemy
from app.domain.models.user import User
from app.domain.models.job import Job
from app.domain.models.file import File
from app.domain.models.cloud_connection import CloudConnection

logger = logging.getLogger(__name__)

# Wrapper to inject DB session
async def execute_pipeline(ctx, job_id: str):
    logger.info(f"Worker processing job {job_id}")
    
    sentry_sdk.set_tag("job_id", job_id)
    sentry_sdk.set_context("job", {"job_id": job_id})

    # run_pipeline is synchronous (uses blocking I/O), so we run it in a thread
    # to avoid blocking the async worker loop.
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, run_pipeline, job_id, SessionLocal)
    logger.info(f"Worker finished job {job_id}")

async def run_retention_cleanup(ctx):
    """Periodic cleanup of expired files for free-tier users."""
    logger.info("Running scheduled retention cleanup")
    try:
        service = RetentionService()
        service.cleanup_expired_files(dry_run=False)
    except Exception as e:
        logger.exception("Retention cleanup failed")
        sentry_sdk.capture_exception(e)

class WorkerSettings:
    functions = [execute_pipeline]
    cron_jobs = [
        # Run retention cleanup daily at 03:00 UTC
        cron(run_retention_cleanup, hour=3, minute=0),
    ]
    redis_settings = redis_settings
    # Increased from 5 to 30 to stay within Upstash free tier (500K commands/month).
    # poll_delay=5 burns ~518K commands/month just from polling.
    # poll_delay=30 uses ~86K commands/month for polling.
    poll_delay = 30
    
    async def on_startup(self):
        # Initialize Sentry for the worker process
        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            sentry_sdk.init(
                dsn=sentry_dsn,
                send_default_pii=True,
                integrations=[
                    LoggingIntegration(
                        level=logging.INFO,
                        event_level=logging.ERROR,
                    )
                ],
            )
        logger.info("Worker started")

    async def on_shutdown(self):
        logger.info("Worker shutting down")
