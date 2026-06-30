from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class BaseEvent(BaseModel):
    idempotency_key: UUID
    event_type: str
    occurred_at: datetime
    payload: dict
