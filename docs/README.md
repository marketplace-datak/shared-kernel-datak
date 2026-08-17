# Документация `shared-kernel-datak`

`shared-kernel-datak` — это библиотека для асинхронной работы с RabbitMQ и PostgreSQL в микросервисной архитектуре маркетплейса. Библиотека предоставляет:

- общие Pydantic-модели событий и реестр событий по `routing_key`
- декларацию topology RabbitMQ
- `Worker` для идемпотентного приёма входящих событий из RabbitMQ в PostgreSQL
- `Worker.publish` для отправки исходящих событий в RabbitMQ

## Оглавление

1. [Быстрый старт](quickstart.md)
2. [Worker](worker.md)
3. [События и реестр](events.md)
4. [Topology RabbitMQ](topology.md)
5. [Тестирование](testing.md)

## Кратко о возможностях

```python
import asyncio
from datetime import UTC, datetime
from uuid import UUID

from shared_kernel import Worker
from shared_kernel.config.topology import Q_B2C_PRODUCT_APPROVED
from shared_kernel.worker import ConsumerConfig
from shared_kernel.models.events import ProductApproved
from shared_kernel.models.events.payloads.moderation import ProductApprovedPayload
from shared_kernel.models.events.payloads.snapshots import (
    ProductSnapshot,
    ProductSnapshotCategory,
)


async def handler(event: ProductApproved) -> None:
    print(f"Received {event.routing_key}: {event.payload.product_id}")


async def main() -> None:
    worker = Worker(
        postgres_url="postgresql+asyncpg://user:pass@localhost:5432/app",
        rabbitmq_url="amqp://guest:guest@localhost/",
        consumer=ConsumerConfig(queues=[Q_B2C_PRODUCT_APPROVED]),
    )

    await worker.start(handler)
    await worker.publish(
        ProductApproved(
            idempotency_key=UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded807"),
            occurred_at=datetime.now(UTC),
            routing_key="product.approved",
            payload=ProductApprovedPayload(
                product_id=UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded808"),
                product=ProductSnapshot(
                    id=UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded808"),
                    seller_id=UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded809"),
                    category_id=UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded810"),
                    title="Product",
                    slug="product",
                    status="ACTIVE",
                    category=ProductSnapshotCategory(
                        id=UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded811"),
                        name="Category",
                    ),
                ),
            ),
        )
    )
    await worker.stop()


asyncio.run(main())
```

## Архитектура в одной схеме

```
┌──────────────┐
│  Publisher   │  (другой микросервис)
└──────┬───────┘
       │ AMQP
       ▼
┌──────────────┐
│   RabbitMQ   │  Exchange / Queue
└──────┬───────┘
       │ consume
       ▼
┌──────────────────────────────┐
│ Worker                       │
│  ┌──────────┐  ┌──────────┐  │
│  │  Rabbit  │  │ Postgres │  │
│  │ transport│  │  inbox   │  │
│  └────┬─────┘  └────┬─────┘  │
│       │             │        │
│       └─── handler ─┘        │
└──────────────────────────────┘
```

Подробности по каждой зоне — в соответствующих разделах документации.
