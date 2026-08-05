from datetime import UTC, datetime
from uuid import UUID

from shared_kernel.models.events import InboxEvent, InboxEventStatusEnum

from ..doubles.in_memory_inbox_repository import InMemoryInboxRepository


def _make_inbox_event(idempotency_key: UUID) -> InboxEvent:
    return InboxEvent(
        idempotency_key=idempotency_key,
        routing_key="product.approved",
        payload={"product_id": "9dcfdd17-4566-4d26-b2f6-e9d0feded808"},
        event_type="product.approved",
        occurred_at=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
    )


class TestSaveIfNew:
    async def test_returns_true_first_time(self) -> None:
        repo = InMemoryInboxRepository()
        event = _make_inbox_event(UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded807"))

        result = await repo.save_if_new(event)

        assert result is True
        assert len(repo.rows) == 1
        assert repo.rows[0].status == InboxEventStatusEnum.PENDING

    async def test_returns_false_for_duplicate_idempotency_key(self) -> None:
        repo = InMemoryInboxRepository()
        event = _make_inbox_event(UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded807"))

        first = await repo.save_if_new(event)
        second = await repo.save_if_new(event)

        assert first is True
        assert second is False
        assert len(repo.rows) == 1


class TestMarkProcessed:
    async def test_updates_status(self) -> None:
        repo = InMemoryInboxRepository()
        key = UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded807")
        await repo.save_if_new(_make_inbox_event(key))

        await repo.mark_processed(key)

        assert repo.rows[0].status == InboxEventStatusEnum.PROCESSED
        assert repo.rows[0].error_message is None


class TestMarkFailed:
    async def test_updates_status_with_error_message(self) -> None:
        repo = InMemoryInboxRepository()
        key = UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded807")
        await repo.save_if_new(_make_inbox_event(key))

        await repo.mark_failed(key, "boom")

        assert repo.rows[0].status == InboxEventStatusEnum.FAILED
        assert repo.rows[0].error_message == "boom"


class TestSaveFailedMessage:
    async def test_creates_new_failed_record_without_idempotency_key(self) -> None:
        repo = InMemoryInboxRepository()

        await repo.save_failed_message(
            routing_key="unknown",
            raw_payload="not-json",
            error_message="ValueError: bad",
        )

        assert len(repo.rows) == 1
        assert repo.rows[0].status == InboxEventStatusEnum.FAILED
        assert repo.rows[0].raw_payload == "not-json"
        assert repo.rows[0].error_message == "ValueError: bad"
        assert repo.rows[0].idempotency_key is None

    async def test_updates_existing_record_by_idempotency_key(self) -> None:
        repo = InMemoryInboxRepository()
        key = UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded807")
        await repo.save_if_new(_make_inbox_event(key))

        await repo.save_failed_message(
            routing_key="product.approved",
            raw_payload="raw",
            error_message="boom",
            idempotency_key=key,
        )

        assert len(repo.rows) == 1
        assert repo.rows[0].status == InboxEventStatusEnum.FAILED
        assert repo.rows[0].error_message == "boom"
        assert repo.rows[0].raw_payload == "raw"
