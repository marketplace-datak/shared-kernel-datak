from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from aio_pika.abc import AbstractIncomingMessage
from shared_kernel.models.events import Event


@dataclass
class IncomingMessageStub:
    body: bytes
    routing_key: str
    content_type: str = "application/json"
    message_id: str | None = None
    acked: bool = False
    rejected: bool = False
    process_calls: int = 0

    @asynccontextmanager
    async def process(self, *, ignore_processed: bool = False) -> AsyncIterator[None]:
        self.process_calls += 1
        if self.acked or self.rejected:
            if ignore_processed:
                yield
                return
            raise RuntimeError("Message already processed")
        try:
            yield
        except Exception:
            self.rejected = True
            raise
        else:
            self.acked = True


@dataclass
class StubMessageTransport:
    connect_calls: int = 0
    close_calls: int = 0
    start_consuming_calls: int = 0
    published: list[Event] = field(default_factory=list)
    _consuming: bool = False
    _handler: Callable[[AbstractIncomingMessage], Awaitable[None]] | None = None

    async def connect(self) -> None:
        self.connect_calls += 1

    async def start_consuming(
        self, handler: Callable[[AbstractIncomingMessage], Awaitable[None]]
    ) -> None:
        self.start_consuming_calls += 1
        self._handler = handler
        self._consuming = True

    async def publish(self, event: Event) -> None:
        self.published.append(event)

    async def close(self) -> None:
        self.close_calls += 1
        self._consuming = False
        self._handler = None

    async def deliver(self, message: IncomingMessageStub) -> None:
        if self._handler is None:
            raise RuntimeError("Transport is not consuming")
        await self._handler(message)
