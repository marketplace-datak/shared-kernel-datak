from .event import register_event, EventTypeEnum
from .snapshots import ProductSnapshot

from pydantic import BaseModel, Field
from uuid import UUID


@register_event(EventTypeEnum.PRODUCT_CREATED)
class EventProductCreated(BaseModel):
    product_id: UUID
    seller_id: UUID
    category_id: UUID
    queue_priority: int = Field(default=3, ge=3, le=4)
    json_after: ProductSnapshot


@register_event(EventTypeEnum.PRODUCT_EDITED)
class EventProductEdited(BaseModel):
    product_id: UUID
    seller_id: UUID
    category_id: UUID | None = None
    queue_priority: int = Field(default=3, ge=1, le=4)
    json_before: ProductSnapshot
    json_after: ProductSnapshot


@register_event(EventTypeEnum.PRODUCT_DELETED)
class EventProductDeletedBySeller(BaseModel):
    product_id: UUID


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
