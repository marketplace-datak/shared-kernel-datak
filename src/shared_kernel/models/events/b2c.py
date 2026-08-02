from . import payloads
from .event import Event


@Event.register()
class OrderFulfilled(Event):
    routing_key: str = "order.fulfilled"
    payload: payloads.OrderFulfilledPayload
