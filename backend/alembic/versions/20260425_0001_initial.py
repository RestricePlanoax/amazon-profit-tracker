"""Initial schema for Amazon Seller Profit Tracker."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260425_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "stores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("marketplace", sa.String(length=64), nullable=False, server_default="amazon_in"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_stores_user_id"), "stores", ["user_id"], unique=False)

    op.create_table(
        "uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("upload_type", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_uploads_store_id"), "uploads", ["store_id"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("cogs", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("store_id", "sku", name="uq_products_store_sku"),
    )
    op.create_index(op.f("ix_products_store_id"), "products", ["store_id"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("order_id", sa.String(length=128), nullable=True),
        sa.Column("units", sa.Integer(), nullable=False),
        sa.Column("revenue", sa.Numeric(12, 2), nullable=False),
        sa.Column("fees", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("refund", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_orders_order_date"), "orders", ["order_date"], unique=False)
    op.create_index(op.f("ix_orders_sku"), "orders", ["sku"], unique=False)
    op.create_index(op.f("ix_orders_store_id"), "orders", ["store_id"], unique=False)

    op.create_table(
        "ads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("spend", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("sales", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_ads_date"), "ads", ["date"], unique=False)
    op.create_index(op.f("ix_ads_sku"), "ads", ["sku"], unique=False)
    op.create_index(op.f("ix_ads_store_id"), "ads", ["store_id"], unique=False)

    op.create_table(
        "daily_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("revenue", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("ad_spend", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("fees", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("refund", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("cogs", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("net_profit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("orders_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("units_sold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("store_id", "date", name="uq_daily_metrics_store_date"),
    )
    op.create_index(op.f("ix_daily_metrics_date"), "daily_metrics", ["date"], unique=False)
    op.create_index(
        op.f("ix_daily_metrics_store_id"), "daily_metrics", ["store_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_daily_metrics_store_id"), table_name="daily_metrics")
    op.drop_index(op.f("ix_daily_metrics_date"), table_name="daily_metrics")
    op.drop_table("daily_metrics")

    op.drop_index(op.f("ix_ads_store_id"), table_name="ads")
    op.drop_index(op.f("ix_ads_sku"), table_name="ads")
    op.drop_index(op.f("ix_ads_date"), table_name="ads")
    op.drop_table("ads")

    op.drop_index(op.f("ix_orders_store_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_sku"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_date"), table_name="orders")
    op.drop_table("orders")

    op.drop_index(op.f("ix_products_store_id"), table_name="products")
    op.drop_table("products")

    op.drop_index(op.f("ix_uploads_store_id"), table_name="uploads")
    op.drop_table("uploads")

    op.drop_index(op.f("ix_stores_user_id"), table_name="stores")
    op.drop_table("stores")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
