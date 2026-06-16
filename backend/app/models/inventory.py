from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("store_id", "sku", "snapshot_date", name="uq_inventory_store_sku_snapshot"),
        UniqueConstraint("store_id", "source_row_hash", name="uq_inventory_store_source_row_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
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
    sku: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    available_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inbound_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    days_in_storage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    monthly_storage_fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    store = relationship("Store", back_populates="inventory_snapshots")
