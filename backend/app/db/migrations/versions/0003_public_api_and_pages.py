"""Add API keys, pages and superuser flag"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_public_api_and_pages"
down_revision = "0002_stripe_plan_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "audit_runs",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.alter_column("audit_runs", "created_at", server_default=None)

    op.add_column(
        "users",
        sa.Column(
            "is_superuser",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("users", "is_superuser", server_default=None)

    op.create_table(
        "pages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_unique_constraint("uq_pages_slug", "pages", ["slug"])

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("prefix", sa.String(length=16), nullable=False),
        sa.Column("hashed_key", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
    )
    op.create_unique_constraint("uq_api_keys_prefix", "api_keys", ["prefix"])


def downgrade() -> None:
    op.drop_column("audit_runs", "created_at")
    op.drop_constraint("uq_api_keys_prefix", "api_keys", type_="unique")
    op.drop_table("api_keys")
    op.drop_constraint("uq_pages_slug", "pages", type_="unique")
    op.drop_table("pages")
    op.drop_column("users", "is_superuser")
