from pydantic import BaseModel
from datetime import datetime

class UserUpdate(BaseModel):
    is_company: bool | None = None
    country: str | None = None
    vat_number: str | None = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    plan: str
    credits: int
    is_beta_tester: bool
    is_active: bool
    is_company: bool
    country: str | None
    vat_number: str | None
    connected_providers: list[str] = []
    created_at: datetime

    class Config:
        from_attributes = True
