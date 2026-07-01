import functools
import operator
from typing import Dict, Type, Any
from pydantic import BaseModel, model_validator
from uuid import UUID
from enum import Enum
from datetime import datetime


class EventTypeEnum(str, Enum):
    PRODUCT_BLOCKED = "PRODUCT_BLOCKED"
    PRODUCT_HARD_BLOCKED = "PRODUCT_HARD_BLOCKED"
    PRODUCT_DELETED = "PRODUCT_DELETED"
    SKU_OUT_OF_STOCK = "SKU_OUT_OF_STOCK"
    PRICE_CHANGED = "PRICE_CHANGED"
    SKU_BACK_IN_STOCK = "SKU_BACK_IN_STOCK"
    ORDER_FULFILLED = "ORDER_FULFILLED"
    ORDER_DELIVERED = "ORDER_DELIVERED"


EVENT_REGISTRY: Dict[EventTypeEnum, Type[BaseModel]] = {}


def register_event(event_type: EventTypeEnum):
    def decorator(cls: Type[BaseModel]):
        EVENT_REGISTRY[event_type] = cls
        return cls

    return decorator


@register_event(EventTypeEnum.PRODUCT_BLOCKED)
@register_event(EventTypeEnum.PRODUCT_HARD_BLOCKED)
@register_event(EventTypeEnum.PRODUCT_DELETED)
class EventProductRef(BaseModel):
    product_id: UUID
    reason: str | None = None


@register_event(EventTypeEnum.SKU_OUT_OF_STOCK)
class EventSkuStock(BaseModel):
    product_id: UUID
    sku_id: UUID
    available_quantity: int


@register_event(EventTypeEnum.PRICE_CHANGED)
class EventPriceChanged(BaseModel):
    sku_id: UUID
    product_id: UUID
    old_price: int
    new_price: int


class OrderFulfilledItem(BaseModel):
    sku_id: UUID
    quantity: int


@register_event(EventTypeEnum.ORDER_FULFILLED)
class EventOrderFulfilled(BaseModel):
    order_id: UUID
    buyer_id: UUID


@register_event(EventTypeEnum.ORDER_DELIVERED)
class EventOrderDelivered(BaseModel):
    order_id: UUID
    buyer_id: UUID


EventPayload: type[Any] = functools.reduce(operator.or_, EVENT_REGISTRY.values())


class Event(BaseModel):
    """Base event type, contains metadata. All useful data is in payload"""

    event_type: EventTypeEnum
    idempotency_key: UUID
    occurred_at: datetime
    payload: BaseModel  # Should be EventPayload, will be checked in model_validator

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
