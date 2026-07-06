from uuid import UUID

from payloads import Payload
from snapshots import ProductSnapshot


class ProductApprovedPayload(Payload):
    product_id: UUID
    product: ProductSnapshot


class ProductBlockedPayload(Payload):
    product_id: UUID
    blocking_reason_id: UUID
    moderator_comment: str
    hard_block: bool
