from collections.abc import Awaitable, Callable

from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from ..models.events import Event, InboxEvent
from .config import ConsumerConfig
from .protocols import InboxEventRepositoryProtocol, MessageTransportProtocol
from .storage import (
    InboxEventRepository,
    create_engine_and_session,
    create_inbox_table,
)
from .transport import (
    RabbitTransport,
    extract_idempotency_key,
    extract_occurred_at,
    safe_load_json,
)

EventHandler = Callable[[Event], Awaitable[None]]


class Worker:
    def __init__(
        self,
        *,
        postgres_url: str,
        rabbitmq_url: str,
        consumer: ConsumerConfig,
        declare_rabbit_topology: bool = True,
        repository: InboxEventRepositoryProtocol | None = None,
        transport: MessageTransportProtocol | None = None,
    ) -> None:
        self._postgres_url = postgres_url
        self._rabbitmq_url = rabbitmq_url
        self._consumer = consumer
        self._declare_rabbit_topology = declare_rabbit_topology
        self._external_repository = repository
        self._external_transport = transport
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker | None = None
        self._repository: InboxEventRepositoryProtocol | None = None
        self._transport: MessageTransportProtocol | None = None

    async def connect(self) -> None:
        if self._repository is None:
            if self._external_repository is not None:
                self._repository = self._external_repository
            else:
                self._engine, self._session_factory = create_engine_and_session(
                    self._postgres_url
                )
                await create_inbox_table(self._engine)
                self._repository = InboxEventRepository(self._session_factory)

        if self._transport is None:
            if self._external_transport is not None:
                self._transport = self._external_transport
            else:
                self._transport = RabbitTransport(
                    rabbitmq_url=self._rabbitmq_url,
                    consumer=self._consumer,
                    declare_topology_on_connect=self._declare_rabbit_topology,
                )

        await self._transport.connect()

    async def start(self, handler: EventHandler) -> None:
        await self.connect()
        await self._require_transport().start_consuming(
            lambda message: self._process_message(message, handler)
        )

    async def publish(self, event: Event) -> None:
        await self.connect()
        await self._require_transport().publish(event)

    async def stop(self) -> None:
        if self._transport is not None:
            await self._transport.close()
        self._transport = None

        if self._engine is not None:
            await self._engine.dispose()
        self._engine = None
        self._session_factory = None
        self._repository = None

    async def _process_message(
        self, message: AbstractIncomingMessage, handler: EventHandler
    ) -> None:
        repository = self._require_repository()
        routing_key = message.routing_key
        raw_payload = message.body.decode()

        async with message.process(ignore_processed=True):
            try:
                event = Event.from_json(routing_key, raw_payload)
            except Exception as exc:  # noqa: BLE001
                parsed_payload = safe_load_json(raw_payload)
                await repository.save_failed_message(
                    routing_key=routing_key,
                    raw_payload=raw_payload,
                    error_message=str(exc),
                    idempotency_key=extract_idempotency_key(parsed_payload),
                    occurred_at=extract_occurred_at(parsed_payload),
                )
                return

            inbox_event = InboxEvent(
                idempotency_key=event.idempotency_key,
                routing_key=event.routing_key,
                payload=event.payload.model_dump(mode="json"),
                event_type=event.routing_key,
                occurred_at=event.occurred_at,
            )

            is_new = await repository.save_if_new(inbox_event)
            if not is_new:
                return

            try:
                await handler(event)
            except Exception as exc:  # noqa: BLE001
                await repository.mark_failed(event.idempotency_key, str(exc))
                return

            await repository.mark_processed(event.idempotency_key)

    def _require_repository(self) -> InboxEventRepositoryProtocol:
        if self._repository is None:
            raise RuntimeError("Worker is not connected to PostgreSQL.")
        return self._repository

    def _require_transport(self) -> MessageTransportProtocol:
        if self._transport is None:
            raise RuntimeError("Worker is not connected to RabbitMQ.")
        return self._transport
