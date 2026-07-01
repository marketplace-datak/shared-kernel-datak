from typing import Dict, Type, Any
from pydantic import BaseModel, model_validator
from uuid import UUID
from enum import Enum
from datetime import datetime


class EventTypeEnum(str, Enum):
    # B2B events
    PRODUCT_CREATED = "PRODUCT_CREATED"
    PRODUCT_EDITED = "PRODUCT_EDITED"
    PRODUCT_DELETED = "PRODUCT_DELETED"
    PRODUCT_BLOCKED = "PRODUCT_BLOCKED"
    PRODUCT_HARD_BLOCKED = "PRODUCT_HARD_BLOCKED"
    SKU_OUT_OF_STOCK = "SKU_OUT_OF_STOCK"
    PRICE_CHANGED = "PRICE_CHANGED"
    SKU_BACK_IN_STOCK = "SKU_BACK_IN_STOCK"

    # B2C events
    ORDER_FULFILLED = "ORDER_FULFILLED"
    ORDER_DELIVERED = "ORDER_DELIVERED"

    # Moderation events


EVENT_REGISTRY: Dict[EventTypeEnum, Type[BaseModel]] = {}


def register_event(event_type: EventTypeEnum):
    def decorator(cls: Type[BaseModel]):
        EVENT_REGISTRY[event_type] = cls
        return cls

    return decorator


class Event(BaseModel):
    """Base event type, contains metadata. All useful data is in payload"""

    event_type: EventTypeEnum
    idempotency_key: UUID
    occurred_at: datetime
    payload: BaseModel  # Should be EventPayload, will be checked in model_validator
    routing_key: str

    @model_validator(mode="before")
    @classmethod
    def parse_event(cls, data: Any) -> Any:
        if isinstance(data, dict):
            event_type = data.get("event_type")
            payload_data = data.get("payload")

            if event_type and payload_data and isinstance(payload_data, dict):
                payload_class = EVENT_REGISTRY.get(EventTypeEnum(event_type))

                if payload_class:
                    data["payload"] = payload_class.model_validate(payload_data)
                else:
                    raise ValueError(f"No type registred: {event_type}")

        return data
