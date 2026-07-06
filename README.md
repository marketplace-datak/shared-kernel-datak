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


