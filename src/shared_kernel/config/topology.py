from dataclasses import dataclass
from enum import Enum


class ExchangeType(str, Enum):
    TOPIC = "topic"
    DIRECT = "direct"
    FANOUT = "FANOUT"


@dataclass(frozen=True)
class Exchange:
    name: str
    type: ExchangeType = ExchangeType.TOPIC
    durable: bool = True


@dataclass(frozen=True)
class Queue:
    name: str
    durable = True
    arguments: dict | None = None


@dataclass(frozen=True)
class Binding:
    exchange: Exchange
    queue: Queue
    routing_key: str


# Exchanges
EXCHANGE_B2B_PRODUCTS = Exchange("exchange.b2b.products")
EXCHANGE_MODERATION = Exchange("exchange.b2b.products")
EXCHANGE_B2C_ORDERS = Exchange("exchange.b2b.products")

# Queues
Q_MOD_PRODUCT_UPDATED = Queue("moderation.queue.product.updated")
Q_B2C_PRODUCT_APPROVED = Queue("b2c.queue.product.approved")
Q_B2C_PRODUCT_UNBLOCKED = Queue("b2c.queue.product.unblocked")
Q_B2C_PRODUCT_DELETED = Queue("b2c.queue.product.deleted")
Q_B2C_SKU_QTY_CHANGED = Queue("b2c.queue.sku.quantity_changed")
Q_B2C_SKU_PRICE_CHANGED = Queue("b2c.queue.sku.price_changed")
Q_B2B_PRODUCT_APPROVED = Queue("b2b.queue.product.approved")
Q_B2B_PRODUCT_BLOCKED = Queue("b2b.queue.product.blocked")
Q_B2B_ORDER_PLACED = Queue("b2b.queue.order.placed")
Q_B2B_ORDER_FULFILLED = Queue("b2b.queue.order.fulfilled")


BINDINGS: list[Binding] = [
    # B2B -> Moderation
    Binding(EXCHANGE_B2B_PRODUCTS, Q_MOD_PRODUCT_UPDATED, "product.updated"),
    #
    # B2B -> B2C
    Binding(EXCHANGE_B2B_PRODUCTS, Q_B2C_SKU_PRICE_CHANGED, "sku.price_changed"),
    Binding(EXCHANGE_B2B_PRODUCTS, Q_B2C_SKU_QTY_CHANGED, "sku.quantity_changed"),
    #
    # Moderation -> B2C
    Binding(EXCHANGE_MODERATION, Q_B2C_PRODUCT_APPROVED, "product.approved"),
    Binding(EXCHANGE_MODERATION, Q_B2C_PRODUCT_UNBLOCKED, "product.unblocked"),
    #
    # Moderation -> B2B
    Binding(EXCHANGE_MODERATION, Q_B2B_PRODUCT_APPROVED, "product.approved"),
    Binding(EXCHANGE_MODERATION, Q_B2B_PRODUCT_BLOCKED, "product.blocked"),
    #
    # B2C -> Moderation
    Binding(EXCHANGE_B2C_ORDERS, Q_B2B_ORDER_FULFILLED, "order.fulfilled"),
    Binding(EXCHANGE_B2C_ORDERS, Q_B2B_ORDER_PLACED, "order.placed"),
]

EXCHANGES = {e.name: e for e in set(b.exchange for b in BINDINGS)}
QUEUES = {q.name: q for q in set(b.queue for b in BINDINGS)}
