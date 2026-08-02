from datetime import datetime
from enum import Enum
from typing import Callable
from uuid import UUID

from pydantic import BaseModel

from .payloads import Payload

EVENT_REGISTRY: dict[str, type[Event]] = {}


class Event(BaseModel):
    idempotency_key: UUID
    occurred_at: datetime
    routing_key: str
    payload: Payload

    @classmethod
    def register(cls) -> Callable[[type["Event"]], type["Event"]]:
        """Decorator to register events"""

        def decorator(event_cls: type["Event"]) -> type["Event"]:
            rk = getattr(event_cls, "routing_key", None)
            if rk is None:
                rk = event_cls.model_fields["routing_key"].default

            if rk:
                EVENT_REGISTRY[rk] = event_cls

            return event_cls

        return decorator

    @classmethod
    def from_json(cls, routing_key: str, json_data: str) -> "Event":
        if routing_key not in EVENT_REGISTRY:
            raise ValueError(f"Unknown routing_key: {routing_key}.")

        event_cls = EVENT_REGISTRY[routing_key]
        return event_cls.model_validate_json(json_data)


class OutboxEvent(BaseModel):
    """
    Copy-paste model from service database
    Used to export from library into MS database
    """

    routing_key: str
    idempotency_key: UUID
    event_type: str
    payload: dict
    occurred_at: datetime

    @classmethod
    def from_event(cls, event: Event) -> "OutboxEvent":
        return cls(
            routing_key=event.routing_key,
            idempotency_key=event.idempotency_key,
            event_type=event.routing_key,
            payload=event.payload.model_dump(mode="json"),
            occurred_at=event.occurred_at,
        )


class OutboxEventStatusEnum(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"


class InboxEvent(BaseModel):
    """
    Copy-paste model from service database
    Used to export from library into MS database
    """

    idempotency_key: UUID
    routing_key: str
    payload: dict
    event_type: str
    occurred_at: datetime

    def to_event(self) -> Event:
        if self.routing_key not in EVENT_REGISTRY:
            raise ValueError(f"Unknown routing_key: {self.routing_key}.")

        event_cls = EVENT_REGISTRY[self.routing_key]
        return event_cls(
            idempotency_key=self.idempotency_key,
            occurred_at=self.occurred_at,
            routing_key=self.routing_key,
            payload=self.payload,
        )


class InboxEventStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
