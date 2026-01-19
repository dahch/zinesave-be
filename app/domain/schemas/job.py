from datetime import datetime
from pydantic import BaseModel, HttpUrl

class JobCreate(BaseModel):
    url: HttpUrl

class JobResponse(BaseModel):
    id: str
    source_url: HttpUrl
    status: str
    progress: int
    created_at: datetime
    external_uploads: dict = {}

    class Config:
        from_attributes = True