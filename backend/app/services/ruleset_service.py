from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.ruleset import RuleSet
from app.services.rules_dsl import (
    RuleComposer,
    RuleDefinition,
    RuleDocument,
    RuleDSLParser,
)


@dataclass(slots=True)
class ComposedRuleSet:
    baseline: RuleSet
    override: RuleSet | None
    document: RuleDocument
    rules: list[RuleDefinition]
    yaml: str
    metadata: dict[str, Any]


class RuleSetService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.parser = RuleDSLParser()
        self.composer = RuleComposer()

    # ------------------------------------------------------------------
    def get_latest_global(self) -> RuleSet | None:
        return (
            self.session.query(RuleSet)
            .filter(RuleSet.is_global.is_(True))
            .order_by(RuleSet.created_at.desc(), RuleSet.id.desc())
            .first()
        )

    def get_latest_override(self, org_id: int) -> RuleSet | None:
        return (
            self.session.query(RuleSet)
            .filter(RuleSet.org_id == org_id)
            .order_by(RuleSet.created_at.desc(), RuleSet.id.desc())
            .first()
        )

    # ------------------------------------------------------------------
    def save_global(
        self,
        *,
        yaml_text: str,
        name: str | None = None,
        version: str | None = None,
        created_by: int | None = None,
    ) -> RuleSet:
        document = self.parser.parse(yaml_text)
        record = RuleSet(
            name=name or document.name or "Baseline Global",
            version=version or document.version or self._timestamp_version(),
            is_global=True,
            content=self._build_content(document, yaml_text),
            created_by=created_by,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def save_override(
        self,
        *,
        org_id: int,
        yaml_text: str,
        name: str | None = None,
        version: str | None = None,
        created_by: int | None = None,
    ) -> RuleSet:
        document = self.parser.parse(yaml_text)
        record = RuleSet(
            org_id=org_id,
            name=name or document.name or f"Override org {org_id}",
            version=version or document.version or self._timestamp_version(),
            content=self._build_content(document, yaml_text),
            created_by=created_by,
        )
        self.session.add(record)
        self.session.flush()
        return record

    # ------------------------------------------------------------------
    def compose_for_org(self, org_id: int) -> ComposedRuleSet:
        baseline = self.get_latest_global()
        if not baseline:
            raise ValueError("Nenhum baseline global cadastrado.")

        baseline_doc = self.parser.materialize(baseline.content or {})
        override = self.get_latest_override(org_id)
        override_doc = (
            self.parser.materialize(override.content or {}) if override else RuleDocument()
        )

        rules = self.composer.compose(baseline_doc.rules, override_doc.rules)
        merged_metadata = {**baseline_doc.metadata}
        merged_metadata.update(override_doc.metadata)

        merged_document = RuleDocument(
            name=override_doc.name or baseline_doc.name,
            version=override_doc.version or baseline_doc.version,
            metadata=merged_metadata,
            rules=rules,
        )

        metadata = {
            "sources": {
                "baseline": {"id": baseline.id, "version": baseline.version},
                "override": (
                    {"id": override.id, "version": override.version} if override else None
                ),
            },
            "document": merged_metadata,
        }

        return ComposedRuleSet(
            baseline=baseline,
            override=override,
            document=merged_document,
            rules=rules,
            yaml=merged_document.to_yaml(),
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    def _build_content(self, document: RuleDocument, yaml_text: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "yaml": yaml_text,
            "rules": [rule.to_dict() for rule in document.rules],
        }
        if document.metadata:
            payload["metadata"] = document.metadata
        if document.name:
            payload["name"] = document.name
        if document.version:
            payload["version"] = document.version
        return payload

    def _timestamp_version(self) -> str:
        return datetime.utcnow().strftime("%Y%m%d%H%M%S")
