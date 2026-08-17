import json
from datetime import datetime
from typing import Any
from uuid import UUID


def safe_load_json(raw_payload: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_payload)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def extract_idempotency_key(payload: dict[str, Any]) -> UUID | None:
    raw_value = payload.get("idempotency_key")
    if not isinstance(raw_value, str):
        return None
    try:
        return UUID(raw_value)
    except ValueError:
        return None


def extract_occurred_at(payload: dict[str, Any]) -> datetime | None:
    raw_value = payload.get("occurred_at")
    if not isinstance(raw_value, str):
        return None
    try:
        return datetime.fromisoformat(raw_value)
    except ValueError:
        return None
