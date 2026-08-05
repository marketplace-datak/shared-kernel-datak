from uuid import UUID

from shared_kernel.models.events import InboxEventStatusEnum
from shared_kernel.worker.worker import Worker

from ..doubles.factories import make_event_json_bytes, make_product_approved_event
from ..doubles.stub_message_transport import IncomingMessageStub


class TestInboxFlow:
    async def test_first_event_is_handled_and_marked_processed(
        self,
        worker: Worker,
        inbox_repository,
        transport,
    ) -> None:
        handler_calls: list = []

        async def handler(event) -> None:
            handler_calls.append(event)

        await worker.start(handler)
        event = make_product_approved_event()
        message = IncomingMessageStub(
            body=make_event_json_bytes(event),
            routing_key=event.routing_key,
        )
        await transport.deliver(message)

        assert len(handler_calls) == 1
        assert handler_calls[0].idempotency_key == event.idempotency_key
        assert len(inbox_repository.rows) == 1
        assert inbox_repository.rows[0].status == InboxEventStatusEnum.PROCESSED
        assert message.acked is True
        assert message.rejected is False

    async def test_duplicate_event_is_not_handled_twice(
        self,
        worker: Worker,
        inbox_repository,
        transport,
    ) -> None:
        handler_calls: list = []

        async def handler(event) -> None:
            handler_calls.append(event)

        await worker.start(handler)
        event = make_product_approved_event()
        message_one = IncomingMessageStub(
            body=make_event_json_bytes(event),
            routing_key=event.routing_key,
        )
        message_two = IncomingMessageStub(
            body=make_event_json_bytes(event),
            routing_key=event.routing_key,
        )
        await transport.deliver(message_one)
        await transport.deliver(message_two)

        assert len(handler_calls) == 1
        assert len(inbox_repository.rows) == 1

    async def test_payload_is_preserved_in_inbox(
        self,
        worker: Worker,
        inbox_repository,
        transport,
    ) -> None:
        async def handler(event) -> None:
            return None

        await worker.start(handler)
        event = make_product_approved_event()
        message = IncomingMessageStub(
            body=make_event_json_bytes(event),
            routing_key=event.routing_key,
        )
        await transport.deliver(message)

        row = inbox_repository.rows[0]
        assert row.payload is not None
        assert row.payload["product_id"] == str(event.payload.product_id)
        assert row.routing_key == "product.approved"
        assert row.idempotency_key == UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded807")
