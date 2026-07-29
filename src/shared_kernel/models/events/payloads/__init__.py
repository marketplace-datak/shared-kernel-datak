from pydantic import BaseModel


class Payload(BaseModel):
    pass


from .b2b import (  # noqa: E402
    ProductDeletedPayload,
    ProductUpdatedPayload,
    SkuPriceChangePayload,
    SkuStockChangePayload,
)
from .b2c import OrderFulfilledPayload  # noqa: E402
from .moderation import ProductApprovedPayload, ProductBlockedPayload  # noqa: E402

__all__ = [
    "OrderFulfilledPayload",
    "ProductApprovedPayload",
    "ProductBlockedPayload",
    "ProductDeletedPayload",
    "ProductUpdatedPayload",
    "SkuPriceChangePayload",
    "SkuStockChangePayload",
]
