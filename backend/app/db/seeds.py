from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.models.rule_reference import RuleReference
from app.models.suggestion import Suggestion

DEFAULT_PLANS = [
    {
        "code": "FREE",
        "name": "Free",
        "monthly_price_cents": 0,
        "features": {"exports_pdf": False, "exports_xlsx": False},
        "limits": {"max_xml_uploads_month": 200, "max_storage_mb": 512, "max_users": 3},
    },
    {
        "code": "PRO",
        "name": "Pro",
        "monthly_price_cents": 49900,
        "features": {"exports_pdf": True, "exports_xlsx": True, "rule_dsl_custom": True},
        "limits": {"max_xml_uploads_month": 2000, "max_storage_mb": 5120, "max_users": 10},
    },
]

DEFAULT_SUGGESTIONS = [
    {
        "code": "ST_RATEIO",
        "title": "Recolhimento de ST",
        "body_pt": "Avaliar recolhimento de ST pelo destinatário com base na MVA vigente.",
        "level": "item",
        "requires_accountant_review": True,
    }
]

DEFAULT_REFERENCES = [
    {
        "code": "CONV_142_2018",
        "title": "Convênio ICMS 142/2018",
        "link": "https://www.confaz.fazenda.gov.br/",
        "excerpt": "Dispõe sobre regimes de substituição tributária.",
    }
]


def seed_all(session: Session) -> None:
    for plan_data in DEFAULT_PLANS:
        if not session.query(Plan).filter_by(code=plan_data["code"]).first():
            session.add(Plan(**plan_data))

    for suggestion in DEFAULT_SUGGESTIONS:
        if not session.query(Suggestion).filter_by(code=suggestion["code"]).first():
            session.add(Suggestion(**suggestion))

    for reference in DEFAULT_REFERENCES:
        if not session.query(RuleReference).filter_by(code=reference["code"]).first():
            session.add(RuleReference(**reference))

    session.commit()
