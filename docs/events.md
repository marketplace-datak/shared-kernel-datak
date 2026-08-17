# События и реестр

Библиотека содержит общие Pydantic-модели событий и payload-структур.

## Базовая модель события

Файл: `src/shared_kernel/models/events/event.py`

```python
class Event(BaseModel):
    idempotency_key: UUID
    occurred_at: datetime
    routing_key: str
    payload: Payload
```

### Поля

#### `idempotency_key`

Уникальный ключ события.

Используется для:

- дедупликации входящих сообщений
- безопасной повторной доставки через RabbitMQ
- трассировки одного бизнес-события между сервисами

#### `occurred_at`

Время возникновения события.

#### `routing_key`

Ключ маршрутизации RabbitMQ.

По нему библиотека:

- определяет тип события при десериализации
- определяет exchange при публикации

#### `payload`

Структура зависит от конкретного типа события.

## Реестр событий

Библиотека хранит mapping `routing_key -> Event subclass` в `EVENT_REGISTRY`.

Регистрация выполняется декоратором:

```python
@Event.register()
class ProductApproved(Event):
    routing_key: str = "product.approved"
    payload: payloads.ProductApprovedPayload
```

### Зачем это нужно

Когда worker получает сообщение из RabbitMQ, он знает только:

1. `routing_key`
2. JSON body

Далее библиотека вызывает:

```python
Event.from_json(routing_key, json_data)
```

и восстанавливает конкретный тип события из реестра.

## Текущие типы событий

### B2B

- `SkuStockChanged`
- `SkuPriceChanged`
- `ProductUpdated`
- `ProductDeleted`

### B2C

- `OrderFulfilled`

### Moderation

- `ProductApproved`
- `ProductBlocked`

## Пример создания события

```python
from datetime import UTC, datetime
from uuid import UUID

from shared_kernel.models.events import ProductApproved
from shared_kernel.models.events.payloads.moderation import ProductApprovedPayload
from shared_kernel.models.events.payloads.snapshots import (
    ProductSnapshot,
    ProductSnapshotCategory,
)


event = ProductApproved(
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
```

## Десериализация события

```python
event = Event.from_json(routing_key, json_data)
```

Поведение:

1. если `routing_key` известен, вернется конкретный subclass `Event`
2. если `routing_key` неизвестен, будет `ValueError`
3. если JSON не соответствует модели payload, будет validation error

## `InboxEvent` и `OutboxEvent`

Помимо доменных событий библиотека содержит DTO-модели для persistence-слоев.

### `InboxEvent`

Используется для сохранения входящих событий в inbox-хранилище.

```python
class InboxEvent(BaseModel):
    idempotency_key: UUID
    routing_key: str
    payload: dict
    event_type: str
    occurred_at: datetime
```

### `OutboxEvent`

Используется как общая модель исходящего события для внешнего persistence-слоя.

Сейчас `Worker.publish(...)` публикует события напрямую и не использует outbox-таблицу.

## Как добавить новое событие

1. создать payload-модель в `src/shared_kernel/models/events/payloads/`
2. создать subclass `Event` в нужном модуле
3. указать `routing_key`
4. пометить класс декоратором `@Event.register()`
5. экспортировать его через `__init__.py`
6. если событие нужно публиковать/слушать через Worker, добавить соответствующий binding в topology
