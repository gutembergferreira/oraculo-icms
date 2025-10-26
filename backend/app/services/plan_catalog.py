"""Catálogo centralizado de planos e benefícios."""
from __future__ import annotations

from typing import Iterable

PLAN_CATALOG: list[dict[str, object]] = [
    {
        "code": "FREE",
        "name": "Free",
        "monthly_price_cents": 0,
        "features": {
            "exports_pdf": False,
            "exports_xlsx": False,
            "rules_dsl_custom": False,
            "priority_support": False,
        },
        "limits": {
            "max_xml_uploads_month": 200,
            "max_storage_mb": 512,
            "max_users": 3,
        },
        "stripe_product_handle": "plan_free",
        "stripe_price_lookup_key": None,
    },
    {
        "code": "PRO",
        "name": "Pro",
        "monthly_price_cents": 49900,
        "features": {
            "exports_pdf": True,
            "exports_xlsx": True,
            "rules_dsl_custom": True,
            "priority_support": False,
        },
        "limits": {
            "max_xml_uploads_month": 2000,
            "max_storage_mb": 5120,
            "max_users": 15,
        },
        "stripe_product_handle": "plan_pro",
        "stripe_price_lookup_key": "plan_pro_monthly",
    },
    {
        "code": "BUSINESS",
        "name": "Business",
        "monthly_price_cents": 99900,
        "features": {
            "exports_pdf": True,
            "exports_xlsx": True,
            "rules_dsl_custom": True,
            "priority_support": True,
        },
        "limits": {
            "max_xml_uploads_month": 10000,
            "max_storage_mb": 20480,
            "max_users": 50,
        },
        "stripe_product_handle": "plan_business",
        "stripe_price_lookup_key": "plan_business_monthly",
    },
    {
        "code": "ENTERPRISE",
        "name": "Enterprise",
        "monthly_price_cents": 249900,
        "features": {
            "exports_pdf": True,
            "exports_xlsx": True,
            "rules_dsl_custom": True,
            "priority_support": True,
            "dedicated_success": True,
        },
        "limits": {
            "max_xml_uploads_month": 50000,
            "max_storage_mb": 102400,
            "max_users": 200,
        },
        "stripe_product_handle": "plan_enterprise",
        "stripe_price_lookup_key": "plan_enterprise_monthly",
    },
]


def iter_seed_plans() -> Iterable[dict[str, object]]:
    """Retorna apenas os campos persistidos na tabela de planos."""

    allowed_keys = {"code", "name", "monthly_price_cents", "features", "limits"}
    for plan in PLAN_CATALOG:
        yield {key: plan[key] for key in allowed_keys}
