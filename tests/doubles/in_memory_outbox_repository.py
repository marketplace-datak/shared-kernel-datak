from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from shared_kernel.models.events import OutboxEvent, OutboxEventStatusEnum


@dataclass
class OutboxRow:
    routing_key: str
    idempotency_key: UUID
    event_type: str
    payload: dict
    occurred_at: datetime
    status: OutboxEventStatusEnum
    error_message: str | None = None
    sent_at: datetime | None = None


class InMemoryOutboxRepository:
    def __init__(self) -> None:
        self.rows: list[OutboxRow] = []
        self.sent_calls: list[UUID] = []
        self.failed_calls: list[tuple[UUID, str]] = []

    async def save_if_new(self, event: OutboxEvent) -> bool:
        for row in self.rows:
            if row.idempotency_key == event.idempotency_key:
                return False

        self.rows.append(
            OutboxRow(
                routing_key=event.routing_key,
                idempotency_key=event.idempotency_key,
                event_type=event.event_type,
                payload=event.payload,
                occurred_at=event.occurred_at,
                status=OutboxEventStatusEnum.PENDING,
            )
        )
        return True

    async def mark_sent(self, idempotency_key: UUID) -> None:
        self.sent_calls.append(idempotency_key)
        for row in self.rows:
            if row.idempotency_key == idempotency_key:
                row.status = OutboxEventStatusEnum.SENT
                row.error_message = None
                row.sent_at = datetime.now(UTC)
                return

    async def mark_failed(self, idempotency_key: UUID, error_message: str) -> None:
        self.failed_calls.append((idempotency_key, error_message))
        for row in self.rows:
            if row.idempotency_key == idempotency_key:
                row.status = OutboxEventStatusEnum.FAILED
                row.error_message = error_message
                return

    async def list_pending(self, limit: int) -> list[OutboxEvent]:
        pending_rows = [
            row for row in self.rows if row.status != OutboxEventStatusEnum.SENT
        ][:limit]

        return [
            OutboxEvent(
                routing_key=row.routing_key,
                idempotency_key=row.idempotency_key,
                event_type=row.event_type,
                payload=row.payload,
                occurred_at=row.occurred_at,
            )
            for row in pending_rows
        ]
