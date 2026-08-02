from . import payloads
from .event import Event


@Event.register()
class ProductApproved(Event):
    routing_key: str = "product.approved"
    payload: payloads.ProductApprovedPayload


@Event.register()
class ProductBlocked(Event):
    routing_key: str = "product.blocked"
    payload: payloads.ProductBlockedPayload
