# Тестирование

В библиотеке уже есть базовый pytest-набор, который покрывает:

- парсеры payload
- in-memory inbox repository
- resolve логики exchange по `routing_key`
- основной flow `Worker`
- ошибки handler
- невалидные и неизвестные сообщения

## Запуск тестов

Локально:

```bash
make test
```

или напрямую:

```bash
uv run pytest
```

## Что тестируется

### `tests/storage/test_parsers.py`

Проверяет:

1. разбор JSON в dict
2. корректное извлечение `idempotency_key`
3. корректное извлечение `occurred_at`
4. поведение на невалидном input

### `tests/storage/test_in_memory_repository.py`

Проверяет тестовую in-memory реализацию inbox repository.

Это полезно, потому что:

1. она используется как тестовый дублер для `Worker`
2. она повторяет контракт production-репозитория

### `tests/transport/test_resolve_exchange_name.py`

Проверяет логику определения exchange по `routing_key`.

### `tests/worker/*`

Проверяют основной orchestration-flow:

1. новое сообщение вызывает handler
2. дубликат не вызывает handler повторно
3. успех дает статус `PROCESSED`
4. ошибка handler дает статус `FAILED`
5. невалидный JSON сохраняется как `FAILED`
6. неизвестный `routing_key` сохраняется как `FAILED`

## Почему тесты без RabbitMQ и Postgres

Базовые тесты в библиотеке сделаны как unit-тесты.

Для этого используются тестовые дубли:

- `InMemoryInboxRepository`
- `StubMessageTransport`
- `IncomingMessageStub`

Плюсы такого подхода:

1. тесты быстрые
2. не нужен Docker
3. не нужен настоящий RabbitMQ
4. не нужен настоящий PostgreSQL
5. проще проверять edge-cases и ошибки

## Как тестировать сервис, который использует библиотеку

В прикладном сервисе обычно полезны два слоя тестов.

### Unit-тесты сервиса

На уровне сервиса можно тестировать:

1. собственный `handler(event)`
2. преобразование `Event -> domain command`
3. бизнес-валидацию

В этих тестах `Worker` можно не поднимать, а работать напрямую с event-моделями.

### Integration-тесты сервиса

Если нужно проверить реальную доставку событий, стоит добавить integration-тесты c:

1. RabbitMQ
2. PostgreSQL
3. реальным `Worker`

Обычно это делается через:

- Docker Compose
- testcontainers
- GitHub Actions services

## CI

В репозитории настроен GitHub Actions workflow `.github/workflows/ci.yml`.

На `push` запускаются:

1. lint job
2. test job

Используемые команды:

```bash
make format
make test
```

## Полезные команды разработки

```bash
uv sync --dev
make format
make test
```

Если вы меняете библиотечный код, обычно этого достаточно, чтобы быстро проверить базовую корректность изменений.
