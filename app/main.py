import os
import sentry_sdk
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.api.routes import jobs, auth, me, upload
from app.domain.models import job, job_content, file

Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager
from arq import create_pool
from app.core.queue import redis_settings
from app.core.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await create_pool(redis_settings)
    yield
    await app.state.redis.close()

setup_logging()

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
    integrations=[
        sentry_sdk.integrations.logging.LoggingIntegration(
            level=logging.INFO,        # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )
    ]
)

app = FastAPI(title="Reader -> ePub", description="API for converting reader to epub", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://zinesave-fe-l64v.vercel.app",
        "https://zinesave-fe.vercel.app",
        "https://zanesave.io",
        "https://www.zanesave.io",
    ],
    allow_origin_regex=r"https://zinesave-fe.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(upload.router)

@app.get("/")
def healthcheck():
    return {"status": "ok"}

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0