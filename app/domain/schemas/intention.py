from datetime import datetime

from pydantic import BaseModel


class IntentionCreate(BaseModel):
    tier_requested: str

class IntentionResponse(BaseModel):
    id: str
    user_id: str
    tier_requested: str
    clicked_at: datetime
    reward_granted: bool

    class Config:
        from_attributes = True
