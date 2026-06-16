"""Add batch-safe ingestion fields for advanced analytics imports."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260615_0007"
down_revision = "20260615_0006"
branch_labels = None
depends_on = None


def _add_batch_columns(table_name: str, unique_name: str) -> None:
    op.add_column(
        table_name,
        sa.Column("import_batch_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(table_name, sa.Column("source_row_hash", sa.String(length=128), nullable=True))
    op.create_index(f"ix_{table_name}_import_batch_id", table_name, ["import_batch_id"])
    op.create_index(f"ix_{table_name}_source_row_hash", table_name, ["source_row_hash"])
    op.create_foreign_key(
        f"fk_{table_name}_import_batch_id_import_batches",
        table_name,
        "import_batches",
        ["import_batch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(unique_name, table_name, ["store_id", "source_row_hash"])


def _drop_batch_columns(table_name: str, unique_name: str) -> None:
    op.drop_constraint(unique_name, table_name, type_="unique")
    op.drop_constraint(
        f"fk_{table_name}_import_batch_id_import_batches",
        table_name,
        type_="foreignkey",
    )
    op.drop_index(f"ix_{table_name}_source_row_hash", table_name=table_name)
    op.drop_index(f"ix_{table_name}_import_batch_id", table_name=table_name)
    op.drop_column(table_name, "source_row_hash")
    op.drop_column(table_name, "import_batch_id")


def upgrade() -> None:
    _add_batch_columns("return_analytics", "uq_return_analytics_store_source_row_hash")
    _add_batch_columns("reimbursements", "uq_reimbursements_store_source_row_hash")
    _add_batch_columns("ad_campaign_metrics", "uq_ad_campaign_metrics_store_source_row_hash")

    op.add_column("inventory", sa.Column("days_in_storage", sa.Integer(), nullable=True))
    op.add_column("inventory", sa.Column("monthly_storage_fee", sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("inventory", "monthly_storage_fee")
    op.drop_column("inventory", "days_in_storage")

    _drop_batch_columns("ad_campaign_metrics", "uq_ad_campaign_metrics_store_source_row_hash")
    _drop_batch_columns("reimbursements", "uq_reimbursements_store_source_row_hash")
    _drop_batch_columns("return_analytics", "uq_return_analytics_store_source_row_hash")
