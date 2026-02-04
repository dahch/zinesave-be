import os
import asyncio
import logging
import sentry_sdk
from arq import create_pool
from app.core.database import SessionLocal
from app.services.pipeline_service import run_pipeline
from app.core.queue import redis_settings

# Import models to ensure they are registered with SQLAlchemy
from app.domain.models.user import User
from app.domain.models.job import Job
from app.domain.models.file import File
from app.domain.models.cloud_connection import CloudConnection

# Wrapper to inject DB session
async def execute_pipeline(ctx, job_id: str):
    logger = logging.getLogger(__name__)
    logger.info(f"Worker processing job {job_id}")
    
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("job_id", job_id)
        scope.set_context("job", {"job_id": job_id})

    # run_pipeline is synchronous (uses blocking I/O), so we run it in a thread
    # to avoid blocking the async worker loop.
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, run_pipeline, job_id, SessionLocal)
    logger.info(f"Worker finished job {job_id}")

class WorkerSettings:
    functions = [execute_pipeline]
    redis_settings = redis_settings
    poll_delay = 5
    
    async def on_startup(self):
        logging.getLogger(__name__).info("Worker started")

    async def on_shutdown(self):
        logging.getLogger(__name__).info("Worker shutting down")
