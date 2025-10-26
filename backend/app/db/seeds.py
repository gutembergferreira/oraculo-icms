from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.models.rule_reference import RuleReference
from app.models.suggestion import Suggestion
from app.services.plan_catalog import iter_seed_plans
from app.services.ruleset_service import RuleSetService
from app.services.rule_packs import get_rule_pack

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
    for plan_data in iter_seed_plans():
        if not session.query(Plan).filter_by(code=plan_data["code"]).first():
            session.add(Plan(**plan_data))

    for suggestion in DEFAULT_SUGGESTIONS:
        if not session.query(Suggestion).filter_by(code=suggestion["code"]).first():
            payload = dict(suggestion)
            if "id" in Suggestion.__table__.c:
                next_id = session.execute(
                    select(func.max(Suggestion.__table__.c.id))
                ).scalar()
                payload["id"] = (next_id or 0) + 1
            session.add(Suggestion(**payload))

    for reference in DEFAULT_REFERENCES:
        if not session.query(RuleReference).filter_by(code=reference["code"]).first():
            session.add(RuleReference(**reference))

    rules_service = RuleSetService(session)
    if not rules_service.get_latest_global():
        pack = get_rule_pack("zfm_baseline")
        rules_service.save_global(
            yaml_text=pack.yaml,
            name=pack.name,
            version=pack.version,
        )

    session.commit()
