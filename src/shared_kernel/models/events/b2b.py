import payloads.b2b as payloads
from event import Event


class SkuStockChanged(Event):
    routing_key: str = "sku.stock_change"
    payload: payloads.SkuStockChangePayload


class SkuPriceChanged(Event):
    routing_key: str = "sku.price_change"
    payload: payloads.SkuPriceChangePayload


class ProductUpdated(Event):
    routing_key: str = "product.updated"
    payload: payloads.ProductUpdatedPayload


class ProductDeleted(Event):
    routing_key: str = "product.deleted"
    payload: payloads.ProductDeletedPayload
