from datetime import UTC, datetime, timedelta
from uuid import UUID

from shared_kernel.worker.transport.parsers import (
    extract_idempotency_key,
    extract_occurred_at,
    safe_load_json,
)


class TestSafeLoadJson:
    def test_returns_dict_for_json_object(self) -> None:
        assert safe_load_json('{"a": 1}') == {"a": 1}

    def test_returns_empty_dict_for_invalid_json(self) -> None:
        assert safe_load_json("not json") == {}

    def test_returns_empty_dict_for_json_array(self) -> None:
        assert safe_load_json("[1, 2, 3]") == {}


class TestExtractIdempotencyKey:
    def test_returns_uuid_for_valid_string(self) -> None:
        value = "9dcfdd17-4566-4d26-b2f6-e9d0feded807"
        assert extract_idempotency_key({"idempotency_key": value}) == UUID(value)

    def test_returns_none_when_missing(self) -> None:
        assert extract_idempotency_key({}) is None

    def test_returns_none_when_not_a_string(self) -> None:
        assert extract_idempotency_key({"idempotency_key": 123}) is None

    def test_returns_none_when_invalid_uuid(self) -> None:
        assert extract_idempotency_key({"idempotency_key": "not-a-uuid"}) is None


class TestExtractOccurredAt:
    def test_returns_datetime_for_valid_iso_string(self) -> None:
        result = extract_occurred_at({"occurred_at": "2026-08-03T12:00:00+00:00"})
        assert result == datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)

    def test_returns_none_when_missing(self) -> None:
        assert extract_occurred_at({}) is None

    def test_returns_none_when_not_a_string(self) -> None:
        assert extract_occurred_at({"occurred_at": 123}) is None

    def test_returns_none_when_invalid_format(self) -> None:
        assert extract_occurred_at({"occurred_at": "not-a-date"}) is None

    def test_supports_non_utc_timezone(self) -> None:
        result = extract_occurred_at({"occurred_at": "2026-08-03T15:00:00+03:00"})
        assert result is not None
        assert result.tzinfo is not None
        assert result.utcoffset() == timedelta(hours=3)
