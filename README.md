# Shared kernel
Библиотека для rabbitmq для [Marketplace-datak](https://github.com/saneczkab/marketplace-datak)


# Модули
## Models
Реализует pydantic модели событий, попадающих в RabbitMQ

Схема события
```python
class Event:
    idempotency_key
    occurred_at
    event_type
    payload
```
Структура payload определяется типом события

---
# Список событий
## Moderation
- Product approved
    - To b2b seller notification
    - To b2c to (add/patch) to db 
- Product blocked
    - Blocked = need changes
- Product hard blocked
    - Hard blocked = can't be changed
- Product unblocked

## B2B
- Product upsert
    - Includes both sku and product upserts
    - If product is being sold at the time we hide it in b2c
- Sku quantity change
- Sku price change
- Product deleted
- Product deleted

## B2C
- Order placed
- Order fulfilled

---

# Worker
Библиотека предоставляет `Worker`, который:
- подключается к RabbitMQ и PostgreSQL
- идемпотентно сохраняет входящие события в inbox-таблицу
- передает новые события в `async handler`
- сохраняет ошибки обработки в БД
- умеет публиковать исходящие события в RabbitMQ

Пример использования:

```python
from shared_kernel import Worker
from shared_kernel.config.topology import Q_B2C_PRODUCT_APPROVED
from shared_kernel.models.events import ProductApproved
from shared_kernel.worker import ConsumerConfig


async def handler(event):
    print(event.routing_key)


worker = Worker(
    postgres_url="postgresql+asyncpg://user:password@localhost:5432/app",
    rabbitmq_url="amqp://guest:guest@localhost/",
    consumer=ConsumerConfig(queues=[Q_B2C_PRODUCT_APPROVED]),
)

await worker.start(handler)

event = ProductApproved.model_validate(
    {
        "idempotency_key": "9dcfdd17-4566-4d26-b2f6-e9d0feded807",
        "occurred_at": "2026-08-03T12:00:00+00:00",
        "routing_key": "product.approved",
        "payload": {
            "product_id": "9dcfdd17-4566-4d26-b2f6-e9d0feded808",
            "product": {
                "id": "9dcfdd17-4566-4d26-b2f6-e9d0feded808",
                "seller_id": "9dcfdd17-4566-4d26-b2f6-e9d0feded809",
                "category_id": "9dcfdd17-4566-4d26-b2f6-e9d0feded810",
                "title": "Product",
                "slug": "product",
                "status": "ACTIVE",
                "category": {
                    "id": "9dcfdd17-4566-4d26-b2f6-e9d0feded811",
                    "name": "Category"
                },
                "images": [],
                "characteristics": [],
                "skus": [],
                "field_reports": []
            }
        }
    }
)

await worker.publish(event)
await worker.stop()
```

