"""Add advanced analytics tables for alerts, returns, reimbursements, storage, ads, and insights."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260615_0006"
down_revision = "20260521_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profit_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=True),
        sa.Column("alert_key", sa.String(length=255), nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "alert_key", name="uq_profit_alerts_store_alert_key"),
    )
    op.create_index("ix_profit_alerts_store_id", "profit_alerts", ["store_id"])
    op.create_index("ix_profit_alerts_sku", "profit_alerts", ["sku"])
    op.create_index("ix_profit_alerts_alert_type", "profit_alerts", ["alert_type"])
    op.create_index("ix_profit_alerts_severity", "profit_alerts", ["severity"])
    op.create_index("ix_profit_alerts_resolved", "profit_alerts", ["resolved"])

    op.create_table(
        "product_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_name", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "sku", name="uq_product_variants_store_sku"),
    )
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])
    op.create_index("ix_product_variants_store_id", "product_variants", ["store_id"])

    op.create_table(
        "return_analytics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_variant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("variant", sa.String(length=255), nullable=True),
        sa.Column("return_reason", sa.String(length=255), nullable=True),
        sa.Column("refund_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("returned_units", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("return_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_variant_id"], ["product_variants.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_return_analytics_store_id", "return_analytics", ["store_id"])
    op.create_index("ix_return_analytics_product_variant_id", "return_analytics", ["product_variant_id"])
    op.create_index("ix_return_analytics_sku", "return_analytics", ["sku"])
    op.create_index("ix_return_analytics_variant", "return_analytics", ["variant"])
    op.create_index("ix_return_analytics_return_reason", "return_analytics", ["return_reason"])
    op.create_index("ix_return_analytics_return_date", "return_analytics", ["return_date"])

    op.create_table(
        "reimbursements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("issue_type", sa.String(length=128), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="pending"),
        sa.Column("detected_at", sa.Date(), nullable=False),
        sa.Column("claim_deadline", sa.Date(), nullable=True),
        sa.Column("claimed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("received", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reimbursements_store_id", "reimbursements", ["store_id"])
    op.create_index("ix_reimbursements_sku", "reimbursements", ["sku"])
    op.create_index("ix_reimbursements_issue_type", "reimbursements", ["issue_type"])
    op.create_index("ix_reimbursements_status", "reimbursements", ["status"])
    op.create_index("ix_reimbursements_detected_at", "reimbursements", ["detected_at"])
    op.create_index("ix_reimbursements_claim_deadline", "reimbursements", ["claim_deadline"])

    op.create_table(
        "inventory_aging",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("days_in_storage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monthly_storage_fee", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("warning_level", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "sku", "snapshot_date", name="uq_inventory_aging_store_sku_snapshot"),
    )
    op.create_index("ix_inventory_aging_store_id", "inventory_aging", ["store_id"])
    op.create_index("ix_inventory_aging_sku", "inventory_aging", ["sku"])
    op.create_index("ix_inventory_aging_days_in_storage", "inventory_aging", ["days_in_storage"])
    op.create_index("ix_inventory_aging_snapshot_date", "inventory_aging", ["snapshot_date"])
    op.create_index("ix_inventory_aging_warning_level", "inventory_aging", ["warning_level"])

    op.create_table(
        "ad_campaign_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", sa.String(length=128), nullable=False),
        sa.Column("campaign_name", sa.String(length=255), nullable=True),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("daily_spend", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acos", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("roas", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("conversion_rate", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "store_id",
            "campaign_id",
            "sku",
            "metric_date",
            name="uq_ad_campaign_metrics_store_campaign_sku_date",
        ),
    )
    op.create_index("ix_ad_campaign_metrics_store_id", "ad_campaign_metrics", ["store_id"])
    op.create_index("ix_ad_campaign_metrics_campaign_id", "ad_campaign_metrics", ["campaign_id"])
    op.create_index("ix_ad_campaign_metrics_sku", "ad_campaign_metrics", ["sku"])
    op.create_index("ix_ad_campaign_metrics_metric_date", "ad_campaign_metrics", ["metric_date"])

    op.create_table(
        "seller_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("insight_type", sa.String(length=64), nullable=False, server_default="daily_briefing"),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=False),
        sa.Column("insight_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seller_insights_store_id", "seller_insights", ["store_id"])
    op.create_index("ix_seller_insights_insight_type", "seller_insights", ["insight_type"])
    op.create_index("ix_seller_insights_priority", "seller_insights", ["priority"])

    op.alter_column("profit_alerts", "resolved", server_default=None)
    op.alter_column("return_analytics", "refund_amount", server_default=None)
    op.alter_column("return_analytics", "returned_units", server_default=None)
    op.alter_column("reimbursements", "status", server_default=None)
    op.alter_column("reimbursements", "claimed", server_default=None)
    op.alter_column("reimbursements", "received", server_default=None)
    op.alter_column("inventory_aging", "quantity", server_default=None)
    op.alter_column("inventory_aging", "days_in_storage", server_default=None)
    op.alter_column("inventory_aging", "monthly_storage_fee", server_default=None)
    op.alter_column("inventory_aging", "warning_level", server_default=None)
    op.alter_column("ad_campaign_metrics", "daily_spend", server_default=None)
    op.alter_column("ad_campaign_metrics", "clicks", server_default=None)
    op.alter_column("ad_campaign_metrics", "orders", server_default=None)
    op.alter_column("ad_campaign_metrics", "acos", server_default=None)
    op.alter_column("ad_campaign_metrics", "roas", server_default=None)
    op.alter_column("ad_campaign_metrics", "conversion_rate", server_default=None)
    op.alter_column("seller_insights", "insight_type", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_seller_insights_priority", table_name="seller_insights")
    op.drop_index("ix_seller_insights_insight_type", table_name="seller_insights")
    op.drop_index("ix_seller_insights_store_id", table_name="seller_insights")
    op.drop_table("seller_insights")

    op.drop_index("ix_ad_campaign_metrics_metric_date", table_name="ad_campaign_metrics")
    op.drop_index("ix_ad_campaign_metrics_sku", table_name="ad_campaign_metrics")
    op.drop_index("ix_ad_campaign_metrics_campaign_id", table_name="ad_campaign_metrics")
    op.drop_index("ix_ad_campaign_metrics_store_id", table_name="ad_campaign_metrics")
    op.drop_table("ad_campaign_metrics")

    op.drop_index("ix_inventory_aging_warning_level", table_name="inventory_aging")
    op.drop_index("ix_inventory_aging_snapshot_date", table_name="inventory_aging")
    op.drop_index("ix_inventory_aging_days_in_storage", table_name="inventory_aging")
    op.drop_index("ix_inventory_aging_sku", table_name="inventory_aging")
    op.drop_index("ix_inventory_aging_store_id", table_name="inventory_aging")
    op.drop_table("inventory_aging")

    op.drop_index("ix_reimbursements_claim_deadline", table_name="reimbursements")
    op.drop_index("ix_reimbursements_detected_at", table_name="reimbursements")
    op.drop_index("ix_reimbursements_status", table_name="reimbursements")
    op.drop_index("ix_reimbursements_issue_type", table_name="reimbursements")
    op.drop_index("ix_reimbursements_sku", table_name="reimbursements")
    op.drop_index("ix_reimbursements_store_id", table_name="reimbursements")
    op.drop_table("reimbursements")

    op.drop_index("ix_return_analytics_return_date", table_name="return_analytics")
    op.drop_index("ix_return_analytics_return_reason", table_name="return_analytics")
    op.drop_index("ix_return_analytics_variant", table_name="return_analytics")
    op.drop_index("ix_return_analytics_sku", table_name="return_analytics")
    op.drop_index("ix_return_analytics_product_variant_id", table_name="return_analytics")
    op.drop_index("ix_return_analytics_store_id", table_name="return_analytics")
    op.drop_table("return_analytics")

    op.drop_index("ix_product_variants_store_id", table_name="product_variants")
    op.drop_index("ix_product_variants_product_id", table_name="product_variants")
    op.drop_table("product_variants")

    op.drop_index("ix_profit_alerts_resolved", table_name="profit_alerts")
    op.drop_index("ix_profit_alerts_severity", table_name="profit_alerts")
    op.drop_index("ix_profit_alerts_alert_type", table_name="profit_alerts")
    op.drop_index("ix_profit_alerts_sku", table_name="profit_alerts")
    op.drop_index("ix_profit_alerts_store_id", table_name="profit_alerts")
    op.drop_table("profit_alerts")
