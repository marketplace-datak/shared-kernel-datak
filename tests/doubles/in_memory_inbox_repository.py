from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from shared_kernel.models.events import InboxEvent, InboxEventStatusEnum


@dataclass
class InboxRow:
    idempotency_key: UUID | None
    routing_key: str
    event_type: str
    payload: dict | None
    raw_payload: str | None
    occurred_at: datetime
    status: InboxEventStatusEnum
    error_message: str | None = field(default=None)


class InMemoryInboxRepository:
    def __init__(self) -> None:
        self.rows: list[InboxRow] = []
        self.processed_calls: list[UUID] = []
        self.failed_calls: list[tuple[UUID, str]] = []

    def by_idempotency_key(self) -> dict[UUID, InboxRow]:
        result: dict[UUID, InboxRow] = {}
        for row in self.rows:
            if row.idempotency_key is not None:
                result[row.idempotency_key] = row
        return result

    def by_routing_key(self) -> defaultdict[str, list[InboxRow]]:
        result: defaultdict[str, list[InboxRow]] = defaultdict(list)
        for row in self.rows:
            result[row.routing_key].append(row)
        return result

    async def save_if_new(self, event: InboxEvent) -> bool:
        for row in self.rows:
            if row.idempotency_key == event.idempotency_key:
                return False
        self.rows.append(
            InboxRow(
                idempotency_key=event.idempotency_key,
                routing_key=event.routing_key,
                event_type=event.event_type,
                payload=event.payload,
                raw_payload=None,
                occurred_at=event.occurred_at,
                status=InboxEventStatusEnum.PENDING,
                error_message=None,
            )
        )
        return True

    async def save_failed_message(
        self,
        *,
        routing_key: str,
        raw_payload: str,
        error_message: str,
        idempotency_key: UUID | None = None,
        occurred_at: datetime | None = None,
    ) -> None:
        for row in self.rows:
            if idempotency_key is not None and row.idempotency_key == idempotency_key:
                row.status = InboxEventStatusEnum.FAILED
                row.error_message = error_message
                row.raw_payload = raw_payload
                return

        self.rows.append(
            InboxRow(
                idempotency_key=idempotency_key,
                routing_key=routing_key,
                event_type=routing_key,
                payload=None,
                raw_payload=raw_payload,
                occurred_at=occurred_at or datetime.now(),
                status=InboxEventStatusEnum.FAILED,
                error_message=error_message,
            )
        )

    async def mark_processed(self, idempotency_key: UUID) -> None:
        self.processed_calls.append(idempotency_key)
        for row in self.rows:
            if row.idempotency_key == idempotency_key:
                row.status = InboxEventStatusEnum.PROCESSED
                row.error_message = None
                return

    async def mark_failed(self, idempotency_key: UUID, error_message: str) -> None:
        self.failed_calls.append((idempotency_key, error_message))
        for row in self.rows:
            if row.idempotency_key == idempotency_key:
                row.status = InboxEventStatusEnum.FAILED
                row.error_message = error_message
                return
