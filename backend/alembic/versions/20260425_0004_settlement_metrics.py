"""Add taxes and reimbursements to daily metrics."""

from alembic import op
import sqlalchemy as sa


revision = "20260425_0004"
down_revision = "20260425_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "daily_metrics",
        sa.Column("taxes", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "daily_metrics",
        sa.Column("reimbursements", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.alter_column("daily_metrics", "taxes", server_default=None)
    op.alter_column("daily_metrics", "reimbursements", server_default=None)


def downgrade() -> None:
    op.drop_column("daily_metrics", "reimbursements")
    op.drop_column("daily_metrics", "taxes")
