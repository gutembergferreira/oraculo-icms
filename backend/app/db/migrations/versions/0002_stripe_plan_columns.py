"""Add Stripe metadata and plan limits"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_stripe"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plans",
        sa.Column("stripe_product_id", sa.String(length=255)),
    )
    op.add_column(
        "plans",
        sa.Column("stripe_price_id", sa.String(length=255)),
    )
    op.add_column(
        "org_settings",
        sa.Column(
            "plan_limits",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "org_settings",
        sa.Column(
            "plan_features",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "org_settings",
        sa.Column("usage_period_start", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "org_settings",
        sa.Column("usage_period_end", sa.DateTime(timezone=True)),
    )



def downgrade() -> None:
    op.drop_column("org_settings", "usage_period_end")
    op.drop_column("org_settings", "usage_period_start")
    op.drop_column("org_settings", "plan_features")
    op.drop_column("org_settings", "plan_limits")
    op.drop_column("plans", "stripe_price_id")
    op.drop_column("plans", "stripe_product_id")
