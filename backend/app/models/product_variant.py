from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("store_id", "sku", name="uq_product_variants_store_sku"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    product = relationship("Product", back_populates="variants")
    store = relationship("Store", back_populates="product_variants")
    return_events = relationship("ReturnAnalytics", back_populates="product_variant")
