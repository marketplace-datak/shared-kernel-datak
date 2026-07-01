from .event import register_event, EventTypeEnum

from pydantic import BaseModel
from uuid import UUID


@register_event(EventTypeEnum.ORDER_FULFILLED)
class EventOrderFulfilled(BaseModel):
    order_id: UUID
    buyer_id: UUID


@register_event(EventTypeEnum.ORDER_DELIVERED)
class EventOrderDelivered(BaseModel):
    order_id: UUID
    buyer_id: UUID
