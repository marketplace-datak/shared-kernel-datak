import json

from shared_kernel.models.events import InboxEventStatusEnum
from shared_kernel.worker.worker import Worker

from ..doubles.factories import make_event_json_bytes, make_product_approved_event
from ..doubles.stub_message_transport import IncomingMessageStub


class TestFailedMessages:
    async def test_invalid_json_is_saved_as_failed(
        self,
        worker: Worker,
        inbox_repository,
        transport,
    ) -> None:
        async def handler(event) -> None:
            raise AssertionError("handler should not be called")

        await worker.start(handler)
        message = IncomingMessageStub(
            body=b"not json at all",
            routing_key="product.approved",
        )

        await transport.deliver(message)

        assert len(inbox_repository.rows) == 1
        row = inbox_repository.rows[0]
        assert row.status == InboxEventStatusEnum.FAILED
        assert row.raw_payload == "not json at all"
        assert row.error_message
        assert message.acked is True
        assert message.rejected is False

    async def test_unknown_routing_key_is_saved_as_failed(
        self,
        worker: Worker,
        inbox_repository,
        transport,
    ) -> None:
        async def handler(event) -> None:
            raise AssertionError("handler should not be called")

        await worker.start(handler)
        event = make_product_approved_event()
        body = make_event_json_bytes(event)
        message = IncomingMessageStub(body=body, routing_key="not.registered.key")

        await transport.deliver(message)

        assert len(inbox_repository.rows) == 1
        row = inbox_repository.rows[0]
        assert row.status == InboxEventStatusEnum.FAILED
        assert row.routing_key == "not.registered.key"
        assert row.raw_payload == body.decode()
        assert message.acked is True
        assert message.rejected is False

    async def test_failed_record_uses_idempotency_key_from_payload_when_present(
        self,
        worker: Worker,
        inbox_repository,
        transport,
    ) -> None:
        async def handler(event) -> None:
            raise AssertionError("handler should not be called")

        await worker.start(handler)
        payload = {
            "idempotency_key": "9dcfdd17-4566-4d26-b2f6-e9d0feded807",
            "occurred_at": "2026-08-03T12:00:00+00:00",
        }
        message = IncomingMessageStub(
            body=json.dumps(payload).encode(),
            routing_key="not.registered.key",
        )

        await transport.deliver(message)

        assert len(inbox_repository.rows) == 1
        row = inbox_repository.rows[0]
        assert row.idempotency_key is not None
        assert str(row.idempotency_key) == "9dcfdd17-4566-4d26-b2f6-e9d0feded807"
        assert row.status == InboxEventStatusEnum.FAILED
