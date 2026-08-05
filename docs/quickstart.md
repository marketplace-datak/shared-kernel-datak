# Быстрый старт

## Установка

Библиотека использует:

- Python `3.14+`
- RabbitMQ
- PostgreSQL
- драйвер `asyncpg`

Если библиотека подключается как зависимость другого сервиса, достаточно установить пакет и его зависимости.

## Минимальный сценарий

Ниже пример сервиса, который:

1. подключается к PostgreSQL и RabbitMQ
2. слушает очередь `Q_B2C_PRODUCT_APPROVED`
3. обрабатывает входящие события `product.approved`
4. умеет публиковать исходящие события

```python
import asyncio
from uuid import UUID
from datetime import datetime, UTC

from shared_kernel import Worker
from shared_kernel.config.topology import Q_B2C_PRODUCT_APPROVED
from shared_kernel.models.events import ProductApproved
from shared_kernel.models.events.payloads.moderation import ProductApprovedPayload
from shared_kernel.models.events.payloads.snapshots import (
    ProductSnapshot,
    ProductSnapshotCategory,
)
from shared_kernel.worker import ConsumerConfig


async def handler(event: ProductApproved) -> None:
    print("received event", event.routing_key, event.payload.product_id)


def build_event() -> ProductApproved:
    return ProductApproved(
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


async def main() -> None:
    worker = Worker(
        postgres_url="postgresql+asyncpg://user:password@localhost:5432/app",
        rabbitmq_url="amqp://guest:guest@localhost/",
        consumer=ConsumerConfig(
            queues=[Q_B2C_PRODUCT_APPROVED],
            prefetch_count=100,
        ),
    )

    await worker.start(handler)
    await worker.publish(build_event())

    # В реальном сервисе здесь обычно долгоживущий процесс.
    await asyncio.sleep(60)
    await worker.stop()


asyncio.run(main())
```

## Что делает `Worker`

При `start(handler)` библиотека делает следующее:

1. создает подключение к PostgreSQL
2. создает inbox-таблицу, если ее еще нет
3. подключается к RabbitMQ
4. идемпотентно объявляет topology RabbitMQ
5. начинает слушать указанные очереди
6. при получении сообщения:
   - пытается распарсить его в `Event`
   - сохраняет его в inbox-таблицу
   - если это новый `idempotency_key`, вызывает `handler`
   - если обработка успешна, ставит статус `PROCESSED`
   - если обработка падает, ставит статус `FAILED` и сохраняет текст ошибки

## Что нужно помнить

1. `handler` должен быть `async`
2. входящие сообщения подтверждаются библиотекой автоматически
3. повторы по одному `idempotency_key` не обрабатываются повторно
4. `publish(event)` публикует событие напрямую в RabbitMQ
5. исходящий outbox в текущей версии библиотеки не реализован

## Следующие шаги

1. [Worker](worker.md) — полный lifecycle и поведение при ошибках
2. [События и реестр](events.md) — как описывать и использовать события
3. [Topology RabbitMQ](topology.md) — как библиотека понимает exchange и queue
