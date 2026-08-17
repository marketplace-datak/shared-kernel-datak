from shared_kernel.models.events import OutboxEvent, OutboxEventStatusEnum
from shared_kernel.worker.worker import Worker

from ..doubles.factories import make_product_approved_event


class TestOutboxPublish:
    async def test_publish_saves_and_marks_sent(
        self,
        worker: Worker,
        outbox_repository,
        transport,
    ) -> None:
        event = make_product_approved_event()

        await worker.publish(event)

        assert len(outbox_repository.rows) == 1
        row = outbox_repository.rows[0]
        assert row.idempotency_key == event.idempotency_key
        assert row.status == OutboxEventStatusEnum.SENT
        assert row.sent_at is not None
        assert len(transport.published) == 1

    async def test_publish_marks_failed_when_transport_fails(
        self,
        worker: Worker,
        outbox_repository,
        transport,
    ) -> None:
        event = make_product_approved_event()
        transport.publish_errors.append(RuntimeError("rabbit down"))

        try:
            await worker.publish(event)
        except RuntimeError as exc:
            assert str(exc) == "rabbit down"
        else:
            raise AssertionError("publish should propagate transport error")

        assert len(outbox_repository.rows) == 1
        row = outbox_repository.rows[0]
        assert row.status == OutboxEventStatusEnum.FAILED
        assert row.error_message == "rabbit down"
        assert len(transport.published) == 0


class TestFlushOutbox:
    async def test_flush_outbox_retries_unsent_events(
        self,
        worker: Worker,
        outbox_repository,
        transport,
    ) -> None:
        event = make_product_approved_event()
        await outbox_repository.save_if_new(OutboxEvent.from_event(event))

        sent_count = await worker.flush_outbox()

        assert sent_count == 1
        assert len(transport.published) == 1
        assert outbox_repository.rows[0].status == OutboxEventStatusEnum.SENT

    async def test_flush_outbox_keeps_failed_status_as_placeholder_when_retry_fails(
        self,
        worker: Worker,
        outbox_repository,
        transport,
    ) -> None:
        event = make_product_approved_event()
        outbox_event = OutboxEvent.from_event(event)
        await outbox_repository.save_if_new(outbox_event)
        transport.publish_errors.append(RuntimeError("still down"))

        sent_count = await worker.flush_outbox()

        assert sent_count == 0
        assert len(transport.published) == 0
        assert outbox_repository.rows[0].status == OutboxEventStatusEnum.FAILED
        assert outbox_repository.rows[0].error_message == "still down"

    async def test_flush_outbox_skips_already_sent_rows(
        self,
        worker: Worker,
        outbox_repository,
        transport,
    ) -> None:
        event = make_product_approved_event()
        await worker.publish(event)

        sent_count = await worker.flush_outbox()

        assert sent_count == 0
        assert len(transport.published) == 1
