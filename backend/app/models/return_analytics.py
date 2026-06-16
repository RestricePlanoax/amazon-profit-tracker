from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow


class ReturnAnalytics(Base):
    __tablename__ = "return_analytics"
    __table_args__ = (
        UniqueConstraint("store_id", "source_row_hash", name="uq_return_analytics_store_source_row_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_row_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    product_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sku: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    variant: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    return_reason: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    returned_units: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    return_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    store = relationship("Store", back_populates="return_events")
    product_variant = relationship("ProductVariant", back_populates="return_events")
