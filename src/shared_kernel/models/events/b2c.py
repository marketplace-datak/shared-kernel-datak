from event import Event
import payloads.b2c as payloads


class OrderFulfilled(Event):
    routing_key: str = "order.fulfilled"
    payload = payloads.OrderFulfilledPayload
