"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-04-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True),
        sa.Column("cnpj", sa.String(length=14), nullable=False),
        sa.Column("zfm_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("monthly_price_cents", sa.Integer(), nullable=False),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("limits", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("mfa_secret", sa.String(length=32)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "rule_references",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("link", sa.String(length=255)),
        sa.Column("excerpt", sa.String(length=500)),
    )

    op.create_table(
        "suggestions",
        sa.Column("code", sa.String(length=50), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body_pt", sa.String(length=1000), nullable=False),
        sa.Column("level", sa.String(length=10), nullable=False),
        sa.Column("requires_accountant_review", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=255)),
        sa.Column("stripe_subscription_id", sa.String(length=255)),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="inactive"),
        sa.Column("current_period_start", sa.DateTime(timezone=True)),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        sa.Column("cancel_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "org_settings",
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), primary_key=True),
        sa.Column("current_plan_id", sa.Integer(), sa.ForeignKey("plans.id")),
        sa.Column("storage_used_mb", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xml_uploaded_count_month", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locale", sa.String(length=10), nullable=False, server_default="pt-BR"),
        sa.Column("billing_email", sa.String(length=255)),
        sa.Column("legal_consent_at", sa.DateTime()),
        sa.Column("flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
    )

    op.create_table(
        "user_org_roles",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), primary_key=True),
        sa.Column("role", sa.String(length=50), nullable=False),
    )

    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("mime", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_backend", sa.String(length=10), nullable=False, server_default="local"),
        sa.Column("storage_path", sa.String(length=255), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("access_key", sa.String(length=44), nullable=False),
        sa.Column("emitente_cnpj", sa.String(length=14), nullable=False),
        sa.Column("destinatario_cnpj", sa.String(length=14), nullable=False),
        sa.Column("uf", sa.String(length=2), nullable=False),
        sa.Column("issue_date", sa.Date()),
        sa.Column("total_value", sa.Numeric(12, 2)),
        sa.Column("freight_value", sa.Numeric(12, 2)),
        sa.Column("has_st", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_file_id", sa.Integer(), sa.ForeignKey("files.id")),
        sa.Column("parsed_at", sa.DateTime()),
        sa.Column("indexed_at", sa.DateTime()),
        sa.UniqueConstraint("access_key", "org_id", name="uq_invoice_access_org"),
    )

    op.create_table(
        "invoice_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("product_code", sa.String(length=60), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("ncm", sa.String(length=8)),
        sa.Column("cest", sa.String(length=7)),
        sa.Column("cfop", sa.String(length=4)),
        sa.Column("cst", sa.String(length=3)),
        sa.Column("quantity", sa.Numeric(14, 4)),
        sa.Column("unit_value", sa.Numeric(14, 4)),
        sa.Column("total_value", sa.Numeric(14, 2)),
        sa.Column("freight_alloc", sa.Numeric(14, 2)),
        sa.Column("discount", sa.Numeric(14, 2)),
        sa.Column("bc_icms", sa.Numeric(14, 2)),
        sa.Column("icms_value", sa.Numeric(14, 2)),
        sa.Column("bc_st", sa.Numeric(14, 2)),
        sa.Column("icms_st_value", sa.Numeric(14, 2)),
        sa.Column("other_taxes", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
    )

    op.create_table(
        "rulesets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id")),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("is_global", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("ruleset_id", sa.Integer(), sa.ForeignKey("rulesets.id")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
    )

    op.create_table(
        "audit_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("audit_run_id", sa.Integer(), sa.ForeignKey("audit_runs.id"), nullable=False),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("invoice_items.id")),
        sa.Column("rule_id", sa.String(length=100), nullable=False),
        sa.Column("inconsistency_code", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=False),
        sa.Column("message_pt", sa.String(length=500), nullable=False),
        sa.Column("suggestion_code", sa.String(length=50)),
        sa.Column("references", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=50)),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("ip", sa.String(length=45)),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
    )

    op.create_index("ix_invoices_org_id", "invoices", ["org_id"])
    op.create_index("ix_invoices_emitente", "invoices", ["emitente_cnpj"])
    op.create_index("ix_invoices_destinatario", "invoices", ["destinatario_cnpj"])
    op.create_index("ix_invoice_items_ncm", "invoice_items", ["ncm"])
    op.create_index("ix_invoice_items_cst", "invoice_items", ["cst"])
    op.create_index("ix_invoice_items_cfop", "invoice_items", ["cfop"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("audit_findings")
    op.drop_table("audit_runs")
    op.drop_table("rulesets")
    op.drop_table("invoice_items")
    op.drop_table("invoices")
    op.drop_table("files")
    op.drop_table("user_org_roles")
    op.drop_table("org_settings")
    op.drop_table("subscriptions")
    op.drop_table("suggestions")
    op.drop_table("rule_references")
    op.drop_table("users")
    op.drop_table("plans")
    op.drop_table("organizations")
