"""Add richer dashboard metric columns."""

from alembic import op
import sqlalchemy as sa


revision = "20260425_0002"
down_revision = "20260425_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "daily_metrics",
        sa.Column("ad_sales", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "daily_metrics",
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "daily_metrics",
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
    )

    op.execute(
        """
        UPDATE daily_metrics dm
        SET
          ad_sales = COALESCE(ads.ad_sales, 0),
          clicks = COALESCE(ads.clicks, 0),
          impressions = COALESCE(ads.impressions, 0)
        FROM (
          SELECT
            store_id,
            date,
            SUM(sales) AS ad_sales,
            SUM(clicks) AS clicks,
            SUM(impressions) AS impressions
          FROM ads
          GROUP BY store_id, date
        ) ads
        WHERE dm.store_id = ads.store_id
          AND dm.date = ads.date
        """
    )

    op.alter_column("daily_metrics", "ad_sales", server_default=None)
    op.alter_column("daily_metrics", "clicks", server_default=None)
    op.alter_column("daily_metrics", "impressions", server_default=None)


def downgrade() -> None:
    op.drop_column("daily_metrics", "impressions")
    op.drop_column("daily_metrics", "clicks")
    op.drop_column("daily_metrics", "ad_sales")
