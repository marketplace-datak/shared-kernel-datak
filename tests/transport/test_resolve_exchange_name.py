import pytest
from shared_kernel.config.topology import Binding, Exchange, Queue
from shared_kernel.worker.transport.rabbit import resolve_exchange_name


def test_resolves_known_routing_key_to_exchange() -> None:
    result = resolve_exchange_name("product.approved")

    assert isinstance(result, str)
    assert result  # non-empty


def test_raises_for_unknown_routing_key() -> None:
    with pytest.raises(ValueError, match="Unknown routing_key"):
        resolve_exchange_name("definitely.not.registered")


def test_raises_for_ambiguous_routing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from shared_kernel.worker.transport import rabbit

    fake_exchange_a = Exchange("exchange.fake.a")
    fake_exchange_b = Exchange("exchange.fake.b")
    fake_queue = Queue("q.fake")
    ambiguous_bindings = [
        Binding(fake_exchange_a, fake_queue, "duplicate.key"),
        Binding(fake_exchange_b, fake_queue, "duplicate.key"),
    ]
    monkeypatch.setattr(rabbit, "BINDINGS", ambiguous_bindings)

    with pytest.raises(ValueError, match="Ambiguous exchange mapping"):
        resolve_exchange_name("duplicate.key")
