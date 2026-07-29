from . import payloads
from .event import Event


@Event.register()
class SkuStockChanged(Event):
    routing_key: str = "sku.stock_change"
    payload: payloads.SkuStockChangePayload


@Event.register()
class SkuPriceChanged(Event):
    routing_key: str = "sku.price_change"
    payload: payloads.SkuPriceChangePayload


@Event.register()
class ProductUpdated(Event):
    routing_key: str = "product.updated"
    payload: payloads.ProductUpdatedPayload


@Event.register()
class ProductDeleted(Event):
    routing_key: str = "product.deleted"
    payload: payloads.ProductDeletedPayload
