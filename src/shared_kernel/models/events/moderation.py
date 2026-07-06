from event import Event
import payloads.moderation as payloads


class ProductApproved(Event):
    routing_key: str = "product.approved"
    payload = payloads.ProductApprovedPayload


class ProductBlocked(Event):
    routing_key: str = "product.blocked"
    payload = payloads.ProductBlockedPayload
