from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow


class Reimbursement(Base):
    __tablename__ = "reimbursements"
    __table_args__ = (
        UniqueConstraint("store_id", "source_row_hash", name="uq_reimbursements_store_source_row_hash"),
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
    sku: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    issue_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="pending", nullable=False, index=True)
    detected_at: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    claim_deadline: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    claimed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    store = relationship("Store", back_populates="reimbursements")
