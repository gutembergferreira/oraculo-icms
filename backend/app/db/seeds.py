# app/db/seeds.py
from app.db import base  # noqa: F401  <-- IMPORTANTE: mantém o registro dos modelos
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import sys
from contextlib import contextmanager
from typing import Iterable

from app.db.session import SessionLocal
from app.models.plan import Plan
from app.models.suggestion import Suggestion
from app.models.rule_reference import RuleReference
from app.services.plan_catalog import iter_seed_plans
from app.services.ruleset_service import RuleSetService
from app.services.rule_packs import get_rule_pack
from app.services.page_service import PageService
from app.models.user import User
from app.core.security import get_password_hash


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


@contextmanager
def get_session() -> Iterable[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def seed_all(session: Session) -> None:
    created_counts = {
        "plans": 0,
        "suggestions": 0,
        "references": 0,
        "ruleset": 0,
        "admin": 0,
        "pages": 0,
    }

    print("==> Seeding: Planos")
    for plan_data in iter_seed_plans():
        code = plan_data["code"]
        exists = session.query(Plan).filter_by(code=code).first()
        if exists:
            print(f"   • Plan {code}: já existia")
        else:
            session.add(Plan(**plan_data))
            created_counts["plans"] += 1
            print(f"   • Plan {code}: criado")

    print("==> Seeding: Sugestões")
    for suggestion in DEFAULT_SUGGESTIONS:
        code = suggestion["code"]
        exists = session.query(Suggestion).filter_by(code=code).first()
        if exists:
            print(f"   • Suggestion {code}: já existia")
        else:
            payload = dict(suggestion)
            # compatibilidade: se tabela tiver 'id' explícito
            if "id" in Suggestion.__table__.c:
                next_id = session.execute(
                    select(func.max(Suggestion.__table__.c.id))
                ).scalar()
                payload["id"] = (next_id or 0) + 1
            session.add(Suggestion(**payload))
            created_counts["suggestions"] += 1
            print(f"   • Suggestion {code}: criada")

    print("==> Seeding: Referências")
    for reference in DEFAULT_REFERENCES:
        code = reference["code"]
        exists = session.query(RuleReference).filter_by(code=code).first()
        if exists:
            print(f"   • Reference {code}: já existia")
        else:
            session.add(RuleReference(**reference))
            created_counts["references"] += 1
            print(f"   • Reference {code}: criada")

    print("==> Seeding: Ruleset Global")
    rules_service = RuleSetService(session)
    if rules_service.get_latest_global():
        print("   • Ruleset global: já existia")
    else:
        pack = get_rule_pack("zfm_baseline")
        rules_service.save_global(
            yaml_text=pack.yaml,
            name=pack.name,
            version=pack.version,
        )
        created_counts["ruleset"] += 1
        print(f"   • Ruleset global '{pack.name}': criado (v{pack.version})")

    print("==> Seeding: Usuário administrador")
    admin_email = "admin@oraculo.app"
    exists_admin = session.query(User).filter(User.email == admin_email).first()
    if exists_admin:
        print(f"   • Admin {admin_email}: já existia")
    else:
        admin_user = User(
            email=admin_email,
            first_name="Admin",
            last_name="Oráculo",
            password_hash=get_password_hash("admin123"),
            is_superuser=True,
        )
        session.add(admin_user)
        created_counts["admin"] += 1
        print(f"   • Admin {admin_email}: criado (senha: admin123)")

    print("==> Seeding: Página inicial")
    page_service = PageService(session)
    page_service.get_or_create(
        "home",
        default_title="Oráculo ICMS",
        default_content=(
            "Centralize a gestão tributária da sua empresa com automações e auditorias em tempo real."
        ),
    )
    created_counts["pages"] += 1  # get_or_create sempre garante a existência
    print("   • Página 'home': ok")

    # commit final garantido por get_session()
    print(
        "\nResumo do seed:",
        f"plans={created_counts['plans']},",
        f"suggestions={created_counts['suggestions']},",
        f"references={created_counts['references']},",
        f"ruleset={created_counts['ruleset']},",
        f"admin={created_counts['admin']},",
        f"pages={created_counts['pages']}",
    )
    sys.stdout.flush()


def main() -> None:
    print("=== Iniciando seed ===")
    with get_session() as session:
        seed_all(session)
    print("=== Seed finalizado ===")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
