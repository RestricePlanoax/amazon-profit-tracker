from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow


class SellerInsight(Base):
    __tablename__ = "seller_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    insight_type: Mapped[str] = mapped_column(String(64), default="daily_briefing", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    insight_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    store = relationship("Store", back_populates="seller_insights")
