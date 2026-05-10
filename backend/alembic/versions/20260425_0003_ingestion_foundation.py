"""Add integrations, sync jobs, settlements, inventory, and upload metadata."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260425_0003"
down_revision = "20260425_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="amazon"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("external_seller_id", sa.String(length=255), nullable=True),
        sa.Column("region", sa.String(length=32), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_integrations_user_id"), "integrations", ["user_id"], unique=False)
    op.create_index(op.f("ix_integrations_store_id"), "integrations", ["store_id"], unique=False)

    op.create_table(
        "sync_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("rows_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_sync_jobs_integration_id"), "sync_jobs", ["integration_id"], unique=False)

    op.create_table(
        "settlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("settlement_date", sa.Date(), nullable=False),
        sa.Column("settlement_id", sa.String(length=128), nullable=True),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("fees", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("taxes", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("reimbursements", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_settlements_store_id"), "settlements", ["store_id"], unique=False)
    op.create_index(op.f("ix_settlements_settlement_date"), "settlements", ["settlement_date"], unique=False)

    op.create_table(
        "inventory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("available_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inbound_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("store_id", "sku", "snapshot_date", name="uq_inventory_store_sku_snapshot"),
    )
    op.create_index(op.f("ix_inventory_store_id"), "inventory", ["store_id"], unique=False)
    op.create_index(op.f("ix_inventory_sku"), "inventory", ["sku"], unique=False)
    op.create_index(op.f("ix_inventory_snapshot_date"), "inventory", ["snapshot_date"], unique=False)

    op.add_column("uploads", sa.Column("import_type", sa.String(length=32), nullable=False, server_default="csv"))
    op.add_column("uploads", sa.Column("file_hash", sa.String(length=128), nullable=True))
    op.add_column("uploads", sa.Column("rows_inserted", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("uploads", sa.Column("rows_skipped", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("uploads", sa.Column("can_reprocess", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index(op.f("ix_uploads_file_hash"), "uploads", ["file_hash"], unique=False)

    op.alter_column("integrations", "provider", server_default=None)
    op.alter_column("integrations", "status", server_default=None)
    op.alter_column("sync_jobs", "status", server_default=None)
    op.alter_column("sync_jobs", "progress_percent", server_default=None)
    op.alter_column("sync_jobs", "rows_processed", server_default=None)
    op.alter_column("settlements", "total_amount", server_default=None)
    op.alter_column("settlements", "fees", server_default=None)
    op.alter_column("settlements", "taxes", server_default=None)
    op.alter_column("settlements", "reimbursements", server_default=None)
    op.alter_column("inventory", "available_units", server_default=None)
    op.alter_column("inventory", "reserved_units", server_default=None)
    op.alter_column("inventory", "inbound_units", server_default=None)
    op.alter_column("uploads", "import_type", server_default=None)
    op.alter_column("uploads", "rows_inserted", server_default=None)
    op.alter_column("uploads", "rows_skipped", server_default=None)
    op.alter_column("uploads", "can_reprocess", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_uploads_file_hash"), table_name="uploads")
    op.drop_column("uploads", "can_reprocess")
    op.drop_column("uploads", "rows_skipped")
    op.drop_column("uploads", "rows_inserted")
    op.drop_column("uploads", "file_hash")
    op.drop_column("uploads", "import_type")

    op.drop_index(op.f("ix_inventory_snapshot_date"), table_name="inventory")
    op.drop_index(op.f("ix_inventory_sku"), table_name="inventory")
    op.drop_index(op.f("ix_inventory_store_id"), table_name="inventory")
    op.drop_table("inventory")

    op.drop_index(op.f("ix_settlements_settlement_date"), table_name="settlements")
    op.drop_index(op.f("ix_settlements_store_id"), table_name="settlements")
    op.drop_table("settlements")

    op.drop_index(op.f("ix_sync_jobs_integration_id"), table_name="sync_jobs")
    op.drop_table("sync_jobs")

    op.drop_index(op.f("ix_integrations_store_id"), table_name="integrations")
    op.drop_index(op.f("ix_integrations_user_id"), table_name="integrations")
    op.drop_table("integrations")
