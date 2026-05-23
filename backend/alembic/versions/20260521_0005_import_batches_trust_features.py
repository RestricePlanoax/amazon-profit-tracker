"""Add import batches and row-level dedupe metadata."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260521_0005"
down_revision = "20260425_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default="csv"),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("import_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("file_hash", sa.String(length=128), nullable=True),
        sa.Column("rows_inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("can_reprocess", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_batches_store_id", "import_batches", ["store_id"])
    op.create_index("ix_import_batches_source_id", "import_batches", ["source_id"])
    op.create_index("ix_import_batches_import_type", "import_batches", ["import_type"])
    op.create_index("ix_import_batches_file_hash", "import_batches", ["file_hash"])

    op.add_column(
        "uploads",
        sa.Column("import_batch_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_uploads_import_batch_id", "uploads", ["import_batch_id"])
    op.create_foreign_key(
        "fk_uploads_import_batch_id_import_batches",
        "uploads",
        "import_batches",
        ["import_batch_id"],
        ["id"],
        ondelete="SET NULL",
    )

    for table_name in ["orders", "ads", "settlements", "inventory"]:
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
        op.create_unique_constraint(
            f"uq_{table_name}_store_source_row_hash",
            table_name,
            ["store_id", "source_row_hash"],
        )

    op.alter_column("import_batches", "source_type", server_default=None)
    op.alter_column("import_batches", "status", server_default=None)
    op.alter_column("import_batches", "rows_inserted", server_default=None)
    op.alter_column("import_batches", "rows_skipped", server_default=None)
    op.alter_column("import_batches", "can_reprocess", server_default=None)


def downgrade() -> None:
    for table_name in ["inventory", "settlements", "ads", "orders"]:
        op.drop_constraint(f"uq_{table_name}_store_source_row_hash", table_name, type_="unique")
        op.drop_constraint(
            f"fk_{table_name}_import_batch_id_import_batches",
            table_name,
            type_="foreignkey",
        )
        op.drop_index(f"ix_{table_name}_source_row_hash", table_name=table_name)
        op.drop_index(f"ix_{table_name}_import_batch_id", table_name=table_name)
        op.drop_column(table_name, "source_row_hash")
        op.drop_column(table_name, "import_batch_id")

    op.drop_constraint("fk_uploads_import_batch_id_import_batches", "uploads", type_="foreignkey")
    op.drop_index("ix_uploads_import_batch_id", table_name="uploads")
    op.drop_column("uploads", "import_batch_id")

    op.drop_index("ix_import_batches_file_hash", table_name="import_batches")
    op.drop_index("ix_import_batches_import_type", table_name="import_batches")
    op.drop_index("ix_import_batches_source_id", table_name="import_batches")
    op.drop_index("ix_import_batches_store_id", table_name="import_batches")
    op.drop_table("import_batches")
