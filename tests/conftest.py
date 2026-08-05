import pytest
from shared_kernel.config.topology import Q_B2C_PRODUCT_APPROVED
from shared_kernel.worker.config import ConsumerConfig
from shared_kernel.worker.worker import Worker

from .doubles.in_memory_inbox_repository import InMemoryInboxRepository
from .doubles.stub_message_transport import StubMessageTransport


@pytest.fixture
def consumer_config() -> ConsumerConfig:
    return ConsumerConfig(queues=[Q_B2C_PRODUCT_APPROVED], prefetch_count=10)


@pytest.fixture
def inbox_repository() -> InMemoryInboxRepository:
    return InMemoryInboxRepository()


@pytest.fixture
def transport() -> StubMessageTransport:
    return StubMessageTransport()


@pytest.fixture
def worker(
    consumer_config: ConsumerConfig,
    inbox_repository: InMemoryInboxRepository,
    transport: StubMessageTransport,
) -> Worker:
    return Worker(
        postgres_url="postgresql+asyncpg://test",
        rabbitmq_url="amqp://test",
        consumer=consumer_config,
        repository=inbox_repository,
        transport=transport,
    )
