from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow


class ProfitAlert(Base):
    __tablename__ = "profit_alerts"
    __table_args__ = (
        UniqueConstraint("store_id", "alert_key", name="uq_profit_alerts_store_alert_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    alert_key: Mapped[str] = mapped_column(String(255), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    resolved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    store = relationship("Store", back_populates="profit_alerts")
