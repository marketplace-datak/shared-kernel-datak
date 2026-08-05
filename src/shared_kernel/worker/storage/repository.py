from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ...models.events import InboxEvent, InboxEventStatusEnum
from .models import InboxEventRecord


class InboxEventRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save_if_new(self, event: InboxEvent) -> bool:
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(InboxEventRecord.id).where(
                    InboxEventRecord.idempotency_key == event.idempotency_key
                )
            )
            if existing is not None:
                return False

            session.add(
                InboxEventRecord(
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
            await session.commit()
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
        async with self._session_factory() as session:
            if idempotency_key is not None:
                existing = await session.scalar(
                    select(InboxEventRecord.id).where(
                        InboxEventRecord.idempotency_key == idempotency_key
                    )
                )
                if existing is not None:
                    await session.execute(
                        update(InboxEventRecord)
                        .where(InboxEventRecord.id == existing)
                        .values(
                            status=InboxEventStatusEnum.FAILED,
                            error_message=error_message,
                            raw_payload=raw_payload,
                            updated_at=datetime.now(UTC),
                        )
                    )
                    await session.commit()
                    return

            session.add(
                InboxEventRecord(
                    idempotency_key=idempotency_key,
                    routing_key=routing_key,
                    event_type=routing_key,
                    payload=None,
                    raw_payload=raw_payload,
                    occurred_at=occurred_at or datetime.now(UTC),
                    status=InboxEventStatusEnum.FAILED,
                    error_message=error_message,
                )
            )
            await session.commit()

    async def mark_processed(self, idempotency_key: UUID) -> None:
        await self._update_status(idempotency_key, InboxEventStatusEnum.PROCESSED, None)

    async def mark_failed(self, idempotency_key: UUID, error_message: str) -> None:
        await self._update_status(
            idempotency_key, InboxEventStatusEnum.FAILED, error_message
        )

    async def _update_status(
        self,
        idempotency_key: UUID,
        status: InboxEventStatusEnum,
        error_message: str | None,
    ) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(InboxEventRecord)
                .where(InboxEventRecord.idempotency_key == idempotency_key)
                .values(
                    status=status,
                    error_message=error_message,
                    updated_at=datetime.now(UTC),
                )
            )
            await session.commit()
