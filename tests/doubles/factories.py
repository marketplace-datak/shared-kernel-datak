from datetime import datetime
from uuid import UUID

from shared_kernel.models.events import Event, ProductApproved
from shared_kernel.models.events.payloads.moderation import ProductApprovedPayload
from shared_kernel.models.events.payloads.snapshots import (
    ProductSnapshot,
    ProductSnapshotCategory,
)


def make_product_approved_event(
    *,
    idempotency_key: UUID | None = None,
    routing_key: str = "product.approved",
    occurred_at: datetime | None = None,
    product_id: UUID | None = None,
) -> ProductApproved:
    return ProductApproved(
        idempotency_key=idempotency_key or UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded807"),
        occurred_at=occurred_at or datetime(2026, 8, 3, 12, 0, 0),
        routing_key=routing_key,
        payload=ProductApprovedPayload(
            product_id=product_id or UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded808"),
            product=_make_product_snapshot(product_id),
        ),
    )


def _make_product_snapshot(product_id: UUID | None) -> ProductSnapshot:
    pid = product_id or UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded808")
    return ProductSnapshot(
        id=pid,
        seller_id=UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded809"),
        category_id=UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded810"),
        title="Product",
        slug="product",
        status="ACTIVE",
        category=ProductSnapshotCategory(
            id=UUID("9dcfdd17-4566-4d26-b2f6-e9d0feded811"),
            name="Category",
        ),
    )


def make_event_json_bytes(event: Event) -> bytes:
    return event.model_dump_json().encode()
