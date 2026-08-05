from collections.abc import Awaitable, Callable

import aio_pika
from aio_pika.abc import AbstractIncomingMessage, AbstractQueue

from ...config.publisher import declare_topology
from ...config.topology import BINDINGS
from ...models.events import Event
from ..config import ConsumerConfig

MessageHandler = Callable[[AbstractIncomingMessage], Awaitable[None]]


def resolve_exchange_name(routing_key: str) -> str:
    exchange_names = {
        binding.exchange.name
        for binding in BINDINGS
        if binding.routing_key == routing_key
    }
    if not exchange_names:
        raise ValueError(f"Unknown routing_key for publishing: {routing_key}.")
    if len(exchange_names) > 1:
        raise ValueError(f"Ambiguous exchange mapping for routing_key: {routing_key}.")
    return exchange_names.pop()


class RabbitTransport:
    def __init__(
        self,
        *,
        rabbitmq_url: str,
        consumer: ConsumerConfig,
        declare_topology_on_connect: bool = True,
    ) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._consumer = consumer
        self._declare_topology_on_connect = declare_topology_on_connect
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._consumers: list[tuple[AbstractQueue, str]] = []

    async def connect(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            return

        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=self._consumer.prefetch_count)

        if self._declare_topology_on_connect:
            await declare_topology(self._connection)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=self._consumer.prefetch_count)

    async def start_consuming(self, handler: MessageHandler) -> None:
        channel = self._require_channel()
        for queue_config in self._consumer.queues:
            queue = await channel.declare_queue(
                name=queue_config.name,
                durable=queue_config.durable,
                arguments=queue_config.arguments,
            )
            consumer_tag = await queue.consume(handler)
            self._consumers.append((queue, consumer_tag))

    async def publish(self, event: Event) -> None:
        channel = self._require_channel()
        exchange_name = resolve_exchange_name(event.routing_key)
        exchange = await channel.get_exchange(exchange_name)

        message = aio_pika.Message(
            body=event.model_dump_json().encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            timestamp=event.occurred_at,
            message_id=str(event.idempotency_key),
        )
        await exchange.publish(message, routing_key=event.routing_key)

    async def close(self) -> None:
        for queue, consumer_tag in self._consumers:
            await queue.cancel(consumer_tag)
        self._consumers.clear()

        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()
        self._channel = None

        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._connection = None

    def _require_channel(self) -> aio_pika.abc.AbstractChannel:
        if self._channel is None:
            raise RuntimeError("RabbitTransport is not connected.")
        return self._channel
