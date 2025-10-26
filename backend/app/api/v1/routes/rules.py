from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.ruleset import RuleSet
from app.models.user import User
from app.schemas import (
    RuleDefinitionSchema,
    RuleEditorPayload,
    RulePackRead,
    RuleSetContent,
    RuleSetRead,
    RuleSetUpsert,
)
from app.services.rule_packs import iter_rule_packs
from app.services.rules_dsl import RuleDSLParseError, RuleDSLValidationError, RuleDSLParser
from app.services.ruleset_service import RuleSetService

router = APIRouter()
_parser = RuleDSLParser()


def _ensure_org_access(user: User, org_id: int) -> None:
    if not any(role.org_id == org_id for role in user.roles):
        raise HTTPException(status_code=403, detail="Acesso negado à organização solicitada.")


def _serialize_ruleset(ruleset: RuleSet) -> RuleSetRead:
    content = ruleset.content or {}
    metadata = content.get("metadata") if isinstance(content, dict) else {}
    yaml_text = content.get("yaml") if isinstance(content, dict) else None
    rules_payload = content.get("rules") if isinstance(content, dict) else None

    if yaml_text is None or rules_payload is None:
        document = _parser.materialize(content if isinstance(content, dict) else {})
        yaml_text = yaml_text or document.to_yaml()
        rules_payload = [rule.to_dict() for rule in document.rules]
        metadata = document.metadata or metadata

    rules = [RuleDefinitionSchema.model_validate(rule) for rule in rules_payload]
    content_model = RuleSetContent(yaml=yaml_text, rules=rules, metadata=metadata or {})

    return RuleSetRead(
        id=ruleset.id,
        name=ruleset.name,
        version=ruleset.version,
        is_global=ruleset.is_global,
        created_at=ruleset.created_at,
        content=content_model,
    )


@router.get("/baseline", response_model=RuleSetRead)
def get_global_baseline(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> RuleSetRead:
    del current_user  # apenas validação de token
    service = RuleSetService(db)
    ruleset = service.get_latest_global()
    if not ruleset:
        raise HTTPException(status_code=404, detail="Baseline global não configurado.")
    return _serialize_ruleset(ruleset)


@router.put("/baseline", response_model=RuleSetRead)
def upsert_global_baseline(
    payload: RuleSetUpsert,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> RuleSetRead:
    service = RuleSetService(db)
    try:
        ruleset = service.save_global(
            yaml_text=payload.yaml,
            name=payload.name,
            version=payload.version,
            created_by=current_user.id,
        )
    except (RuleDSLParseError, RuleDSLValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    return _serialize_ruleset(ruleset)


@router.get("/catalog", response_model=list[RulePackRead])
def list_rule_packs(
    current_user: User = Depends(get_current_user),
) -> list[RulePackRead]:
    del current_user
    return [RulePackRead(**pack.__dict__) for pack in iter_rule_packs()]


@router.get("/orgs/{org_id}", response_model=RuleEditorPayload)
def get_org_rules(
    org_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> RuleEditorPayload:
    _ensure_org_access(current_user, org_id)
    service = RuleSetService(db)
    composed = service.compose_for_org(org_id)
    baseline = _serialize_ruleset(composed.baseline)
    override = _serialize_ruleset(composed.override) if composed.override else None
    effective_rules = [
        RuleDefinitionSchema.model_validate(rule.to_dict()) for rule in composed.rules
    ]
    return RuleEditorPayload(
        baseline=baseline,
        override=override,
        effective_yaml=composed.yaml,
        effective_rules=effective_rules,
        metadata=composed.metadata,
    )


@router.put("/orgs/{org_id}", response_model=RuleSetRead)
def upsert_org_override(
    org_id: int,
    payload: RuleSetUpsert,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> RuleSetRead:
    _ensure_org_access(current_user, org_id)
    service = RuleSetService(db)
    try:
        ruleset = service.save_override(
            org_id=org_id,
            yaml_text=payload.yaml,
            name=payload.name,
            version=payload.version,
            created_by=current_user.id,
        )
    except (RuleDSLParseError, RuleDSLValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    return _serialize_ruleset(ruleset)
