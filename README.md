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
