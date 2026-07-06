from pydantic import BaseModel


class Payload(BaseModel):
    pass


from b2c import OrderFulfilledPayload  # noqa: E402
from b2b import (  # noqa: E402
    ProductDeletedPayload,
    ProductUpdatedPayload,
    SkuStockChangePayload,
    SkuPriceChangePayload,
)
from moderation import ProductApprovedPayload, ProductBlockedPayload  # noqa: E402

__all__ = [
    "ProductDeletedPayload",
    "ProductUpdatedPayload",
    "SkuStockChangePayload",
    "SkuPriceChangePayload",
    "OrderFulfilledPayload",
    "ProductApprovedPayload",
    "ProductBlockedPayload",
]
