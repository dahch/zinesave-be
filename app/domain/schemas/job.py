from datetime import datetime

from pydantic import BaseModel, HttpUrl


class JobCreate(BaseModel):
    url: HttpUrl


class JobCompositeCreate(BaseModel):
    urls: list[HttpUrl]
    title: str


class JobResponse(BaseModel):
    id: str
    source_url: str
    status: str
    progress: int
    created_at: datetime
    external_uploads: dict = {}

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    page: int
    per_page: int
    pages: int
