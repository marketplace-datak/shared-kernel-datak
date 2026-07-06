from uuid import UUID

from snapshots import ProductSnapshot
from payloads import Payload


class ProductUpdatedPayload(Payload):
    product_id: UUID
    seller_id: UUID
    category_id: UUID
    queue_priority: int
    json_before: ProductSnapshot
    json_after: ProductSnapshot


class ProductDeletedPayload(Payload):
    product_id: UUID


class SkuStockChangePayload(Payload):
    product_id: UUID
    sku_id: UUID
    available_quantity: int


class SkuPriceChangePayload(Payload):
    product_id: UUID
    sku_id: UUID
    new_price: int
