from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    marketplace: Mapped[str] = mapped_column(String(64), default="amazon_in", nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    user = relationship("User", back_populates="stores")
    products = relationship(
        "Product",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    uploads = relationship(
        "Upload",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    import_batches = relationship(
        "ImportBatch",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    orders = relationship(
        "Order",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    ads = relationship(
        "Ad",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    daily_metrics = relationship(
        "DailyMetric",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    integrations = relationship(
        "Integration",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    settlements = relationship(
        "Settlement",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    inventory_snapshots = relationship(
        "Inventory",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    product_variants = relationship(
        "ProductVariant",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    return_events = relationship(
        "ReturnAnalytics",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reimbursements = relationship(
        "Reimbursement",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    inventory_aging_rows = relationship(
        "InventoryAging",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    ad_campaign_metrics = relationship(
        "AdCampaignMetric",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    profit_alerts = relationship(
        "ProfitAlert",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    seller_insights = relationship(
        "SellerInsight",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
