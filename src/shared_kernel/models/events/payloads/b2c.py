from uuid import UUID

from . import Payload


class OrderFulfilledPayload(Payload):
    order_id: UUID
    buyer_id: UUID
