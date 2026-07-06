from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class Event(BaseModel):
    idempotency_key: UUID
    occurred_at: datetime
    routing_key: str
