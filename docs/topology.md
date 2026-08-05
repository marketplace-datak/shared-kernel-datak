# Topology RabbitMQ

Библиотека описывает topology RabbitMQ в коде, а затем может идемпотентно объявлять ее при запуске worker.

Файл: `src/shared_kernel/config/topology.py`

## Основные сущности

### `Exchange`

```python
@dataclass(frozen=True)
class Exchange:
    name: str
    type: ExchangeType = ExchangeType.TOPIC
    durable: bool = True
```

### `Queue`

```python
@dataclass(frozen=True)
class Queue:
    name: str
    durable: bool = True
    arguments: dict | None = None
```

### `Binding`

```python
@dataclass(frozen=True)
class Binding:
    exchange: Exchange
    queue: Queue
    routing_key: str
```

## Текущие exchange

- `EXCHANGE_B2B_PRODUCTS`
- `EXCHANGE_MODERATION`
- `EXCHANGE_B2C_ORDERS`

## Текущие queue

Примеры:

- `Q_MOD_PRODUCT_UPDATED`
- `Q_B2C_PRODUCT_APPROVED`
- `Q_B2C_PRODUCT_UNBLOCKED`
- `Q_B2C_PRODUCT_DELETED`
- `Q_B2C_SKU_QTY_CHANGED`
- `Q_B2C_SKU_PRICE_CHANGED`
- `Q_B2B_PRODUCT_APPROVED`
- `Q_B2B_PRODUCT_BLOCKED`
- `Q_B2B_ORDER_PLACED`
- `Q_B2B_ORDER_FULFILLED`

## Объявление topology

Функция:

```python
from shared_kernel.config import declare_topology

await declare_topology(connection)
```

Она:

1. объявляет все exchange из `EXCHANGES`
2. объявляет все queue из `BINDINGS`
3. создает bindings `exchange -> queue -> routing_key`

Операция идемпотентна.

## Как Worker использует topology

### При запуске

Если `declare_rabbit_topology=True`, то `Worker.connect()` вызывает `declare_topology(...)`.

Это позволяет:

1. не создавать exchange и queue вручную в каждом сервисе
2. держать topology в одном месте

### При публикации

Когда вызывается `worker.publish(event)`, библиотека:

1. берет `event.routing_key`
2. находит все `Binding` с этим `routing_key`
3. если найден ровно один exchange, публикует туда
4. если exchange не найден, выбрасывает `ValueError`
5. если найдено несколько exchange, тоже выбрасывает `ValueError`

Это защищает от неоднозначной маршрутизации.

## Как выбрать очереди для consumer

При создании worker вы передаете очереди явно:

```python
from shared_kernel.config.topology import Q_B2C_PRODUCT_APPROVED
from shared_kernel.worker import ConsumerConfig

consumer = ConsumerConfig(
    queues=[Q_B2C_PRODUCT_APPROVED],
    prefetch_count=100,
)
```

Такой подход лучше, чем список строк, потому что:

1. меньше риск опечатки
2. проще поддерживать централизованную topology
3. IDE и type checker лучше понимают API

## Как добавить новый binding

Пример:

```python
NEW_EXCHANGE = Exchange("exchange.new")
NEW_QUEUE = Queue("new.queue.event")

BINDINGS.append(
    Binding(NEW_EXCHANGE, NEW_QUEUE, "new.event")
)
```

После этого:

1. exchange войдет в `EXCHANGES`
2. queue войдет в `QUEUES`
3. `declare_topology(...)` начнет объявлять его автоматически
4. `worker.publish(...)` сможет разрешить exchange для `routing_key="new.event"`, если mapping останется однозначным
