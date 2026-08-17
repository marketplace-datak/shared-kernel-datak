# Worker

`Worker` — это основной orchestration-объект библиотеки.

Он отвечает за:

- подключение к PostgreSQL
- подключение к RabbitMQ
- идемпотентное сохранение входящих сообщений
- вызов пользовательского `async handler`
- публикацию исходящих событий
- сохранение исходящих событий в outbox

## Импорт

```python
from shared_kernel import Worker
from shared_kernel.worker import ConsumerConfig
```

## Конструктор

```python
Worker(
    postgres_url: str,
    rabbitmq_url: str,
    consumer: ConsumerConfig,
    declare_rabbit_topology: bool = True,
)
```

### Параметры

#### `postgres_url`

URL подключения к PostgreSQL через SQLAlchemy async + `asyncpg`.

Пример:

```python
"postgresql+asyncpg://user:password@localhost:5432/app"
```

#### `rabbitmq_url`

AMQP URL для RabbitMQ.

Пример:

```python
"amqp://guest:guest@localhost/"
```

#### `consumer`

Экземпляр `ConsumerConfig`, в котором задаются:

- очереди для прослушивания
- `prefetch_count`

Пример:

```python
from shared_kernel.config.topology import Q_B2C_PRODUCT_APPROVED
from shared_kernel.worker import ConsumerConfig

consumer = ConsumerConfig(
    queues=[Q_B2C_PRODUCT_APPROVED],
    prefetch_count=100,
)
```

#### `declare_rabbit_topology`

Если `True`, при подключении библиотека вызывает `declare_topology(...)` и идемпотентно создает exchange, queue и bindings.

Обычно это стоит оставлять включенным.

## Методы

### `await worker.connect()`

Подготавливает ресурсы, но не запускает потребление сообщений.

Что делает:

1. создает SQLAlchemy engine
2. создает inbox-таблицу
3. создает RabbitMQ connection/channel
4. при необходимости объявляет topology

Используйте, если хотите заранее поднять соединения до вызова `start(...)` или `publish(...)`.

### `await worker.start(handler)`

Подключает worker и регистрирует consumer-обработчики для всех очередей из `ConsumerConfig`.

Сигнатура handler:

```python
async def handler(event: Event) -> None:
    ...
```

Пример:

```python
async def handler(event) -> None:
    print(event.routing_key)


await worker.start(handler)
```

Важно:

1. `start(...)` не завершает процесс сам по себе
2. после `start(...)` сервис должен оставаться живым
3. обычно это означает запуск в долгоживущем приложении или отдельном процессе

### `await worker.publish(event)`

Сохраняет событие в outbox и затем пытается опубликовать его в RabbitMQ.

Пример:

```python
await worker.publish(event)
```

Как библиотека выбирает exchange:

1. берет `event.routing_key`
2. находит соответствующий `Binding` в topology
3. определяет exchange по `routing_key`
4. публикует сообщение с этим `routing_key`

Если `routing_key` неизвестен или соответствует нескольким exchange, будет выброшен `ValueError`.

### Что происходит внутри `publish(...)`

1. создается `OutboxEvent` из доменного `Event`
2. событие сохраняется в PostgreSQL со статусом `PENDING`
3. worker пытается отправить его в RabbitMQ
4. если отправка успешна, запись помечается как `SENT`
5. если отправка падает, запись помечается как `FAILED`, а ошибка пробрасывается наружу

### `await worker.flush_outbox(limit=100)`

Повторно пытается отправить outbox-события, которые еще не были успешно отправлены.

```python
sent_count = await worker.flush_outbox(limit=100)
```

Метод возвращает количество успешно отправленных сообщений.

Текущее поведение:

1. `SENT` записи не трогаются
2. `PENDING` записи пробуются повторно
3. `FAILED` записи тоже участвуют в повторной отправке

Для `FAILED` это пока временная заглушка. Позже сюда можно добавить отдельную политику retry.

### `await worker.stop()`

Закрывает:

1. consumers
2. RabbitMQ connection/channel
3. SQLAlchemy engine

Пример:

```python
await worker.stop()
```

## Модель обработки входящего сообщения

Для каждого входящего сообщения worker делает следующее:

1. читает `routing_key`
2. декодирует `message.body`
3. вызывает `Event.from_json(routing_key, raw_payload)`
4. если событие валидно:
   - конвертирует его в `InboxEvent`
   - сохраняет в inbox-хранилище
   - если это дубликат, handler не вызывается
   - если это новое событие, вызывает `handler`
5. если `handler` завершился успешно:
   - событие помечается как `PROCESSED`
6. если `handler` упал:
   - событие помечается как `FAILED`
   - в `error_message` сохраняется текст исключения

## Поведение при ошибках

### Невалидный JSON

Если сообщение не распарсилось как JSON:

1. запись сохраняется как `FAILED`
2. сохраняется `raw_payload`
3. handler не вызывается

### Неизвестный `routing_key`

Если по `routing_key` не найден зарегистрированный тип события:

1. запись сохраняется как `FAILED`
2. сохраняется `raw_payload`
3. при возможности извлекается `idempotency_key`
4. handler не вызывается

### Ошибка внутри `handler`

Если пользовательский обработчик бросил исключение:

1. событие сохраняется как `FAILED`
2. `error_message` содержит текст исключения
3. сообщение не передается в retry-механику RabbitMQ

Это текущее поведение первой версии библиотеки.

## Inbox-таблица

Сейчас библиотека создает таблицу `shared_kernel_inbox_events`.

В ней хранятся:

- `idempotency_key`
- `routing_key`
- `event_type`
- `payload`
- `raw_payload`
- `occurred_at`
- `status`
- `error_message`
- `created_at`
- `updated_at`

### Статусы

- `PENDING`
- `PROCESSED`
- `FAILED`

## Outbox-таблица

Библиотека также создает таблицу `shared_kernel_outbox_events`.

В ней хранятся:

- `idempotency_key`
- `routing_key`
- `event_type`
- `payload`
- `occurred_at`
- `status`
- `error_message`
- `sent_at`
- `created_at`
- `updated_at`

### Outbox-статусы

- `PENDING`
- `SENT`
- `FAILED`

#### Как понимать `FAILED`

Сейчас `FAILED` означает только то, что последняя попытка отправки завершилась ошибкой.

Это не финальное состояние. В текущей версии `flush_outbox(...)` все равно будет пытаться переотправлять такие события.

## Практические рекомендации

1. Всегда используйте уникальный `idempotency_key` для нового события.
2. Не делайте тяжелую синхронную работу в `handler`.
3. Внутри `handler` лучше писать свою бизнес-логику как идемпотентную.
4. Если нужно отдельное повторное выполнение `FAILED` событий, лучше строить это как отдельный механизм поверх inbox-таблицы.
