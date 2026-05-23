from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    # NeonDB free tier allows ~5 concurrent connections.
    # Keep pool small to avoid connection limit errors,
    # especially since the worker also opens sessions.
    pool_size=2,
    max_overflow=3
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
