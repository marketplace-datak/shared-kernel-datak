from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from aio_pika.abc import AbstractIncomingMessage

from ..models.events import Event, InboxEvent


class InboxEventRepositoryProtocol(Protocol):
    async def save_if_new(self, event: InboxEvent) -> bool: ...

    async def save_failed_message(
        self,
        *,
        routing_key: str,
        raw_payload: str,
        error_message: str,
        idempotency_key: UUID | None = None,
        occurred_at: datetime | None = None,
    ) -> None: ...

    async def mark_processed(self, idempotency_key: UUID) -> None: ...

    async def mark_failed(self, idempotency_key: UUID, error_message: str) -> None: ...


class MessageHandler(Protocol):
    async def __call__(
        self, message: AbstractIncomingMessage
    ) -> None: ...  # pragma: no cover


class MessageTransportProtocol(Protocol):
    async def connect(self) -> None: ...

    async def start_consuming(
        self, handler: Callable[[AbstractIncomingMessage], Awaitable[None]]
    ) -> None: ...

    async def publish(self, event: Event) -> None: ...

    async def close(self) -> None: ...
