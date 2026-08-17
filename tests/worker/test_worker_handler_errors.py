from shared_kernel.models.events import InboxEventStatusEnum
from shared_kernel.worker.worker import Worker

from ..doubles.factories import make_event_json_bytes, make_product_approved_event
from ..doubles.stub_message_transport import IncomingMessageStub


class TestHandlerErrors:
    async def test_handler_exception_saves_failed_status_with_error_message(
        self,
        worker: Worker,
        inbox_repository,
        transport,
    ) -> None:
        async def handler(event) -> None:
            raise ValueError("boom")

        await worker.start(handler)
        event = make_product_approved_event()
        message = IncomingMessageStub(
            body=make_event_json_bytes(event),
            routing_key=event.routing_key,
        )
        await transport.deliver(message)

        assert len(inbox_repository.rows) == 1
        assert inbox_repository.rows[0].status == InboxEventStatusEnum.FAILED
        assert inbox_repository.rows[0].error_message == "boom"

    async def test_handler_exception_is_not_re_raised(
        self,
        worker: Worker,
        inbox_repository,
        transport,
    ) -> None:
        async def handler(event) -> None:
            raise RuntimeError("explode")

        await worker.start(handler)
        event = make_product_approved_event()
        message = IncomingMessageStub(
            body=make_event_json_bytes(event),
            routing_key=event.routing_key,
        )

        await transport.deliver(message)

        assert inbox_repository.rows[0].status == InboxEventStatusEnum.FAILED

    async def test_message_is_acknowledged_after_handler_failure(
        self,
        worker: Worker,
        transport,
    ) -> None:
        async def handler(event) -> None:
            raise ValueError("nope")

        await worker.start(handler)
        event = make_product_approved_event()
        message = IncomingMessageStub(
            body=make_event_json_bytes(event),
            routing_key=event.routing_key,
        )
        await transport.deliver(message)

        assert message.acked is True
        assert message.rejected is False
