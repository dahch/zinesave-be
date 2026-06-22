import logging
from contextlib import asynccontextmanager

import sentry_sdk
from arq import create_pool
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import auth, intentions, jobs, me, upload
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.queue import redis_settings
from app.domain.exceptions import DomainException

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await create_pool(redis_settings)
    yield
    await app.state.redis.close()


setup_logging()

sentry_dsn = settings.SENTRY_DSN
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        send_default_pii=True,
        traces_sample_rate=0.1,
    )

# Rate limiter using in-memory storage (no Redis needed, saves Upstash commands)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Reader -> ePub",
    description="API for converting reader to epub",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    logger.warning(f"Domain exception: {exc.message} (Status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://zinesave-fe-l64v.vercel.app",
        "https://zinesave-fe.vercel.app",
        "https://zinesave.io",
        "https://www.zinesave.io",
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
app.include_router(intentions.router)


@app.get("/")
def healthcheck():
    return {"status": "ok"}


# Only expose sentry-debug in non-production environments
if settings.ENVIRONMENT != "production":

    @app.get("/sentry-debug")
    async def trigger_error():
        raise Exception("Sentry debug error")
