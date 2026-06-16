from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow


class InventoryAging(Base):
    __tablename__ = "inventory_aging"
    __table_args__ = (
        UniqueConstraint("store_id", "sku", "snapshot_date", name="uq_inventory_aging_store_sku_snapshot"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    days_in_storage: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    monthly_storage_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0"),
        nullable=False,
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    warning_level: Mapped[str] = mapped_column(String(32), default="normal", nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    store = relationship("Store", back_populates="inventory_aging_rows")
