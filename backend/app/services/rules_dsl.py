from __future__ import annotations

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable

import yaml


class RuleDSLParseError(ValueError):
    """Erro lançado quando o YAML não pode ser interpretado."""


class RuleDSLValidationError(ValueError):
    """Erro lançado quando a estrutura do DSL é inválida."""


@dataclass(slots=True)
class RuleDefinition:
    id: str
    name: str
    scope: str = "invoice"
    description: str | None = None
    when: dict[str, Any] = field(default_factory=dict)
    then: dict[str, Any] = field(default_factory=dict)
    disabled: bool = False

    def copy(self) -> "RuleDefinition":
        return RuleDefinition(
            id=self.id,
            name=self.name,
            scope=self.scope,
            description=self.description,
            when=deepcopy(self.when),
            then=deepcopy(self.then),
            disabled=self.disabled,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "scope": self.scope,
            "when": deepcopy(self.when),
            "then": deepcopy(self.then),
        }
        if self.description:
            data["description"] = self.description
        if self.disabled:
            data["disabled"] = True
        return data


@dataclass(slots=True)
class RuleDocument:
    name: str | None = None
    version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    rules: list[RuleDefinition] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"rules": [rule.to_dict() for rule in self.rules]}
        if self.name:
            data["name"] = self.name
        if self.version:
            data["version"] = self.version
        if self.metadata:
            data["metadata"] = deepcopy(self.metadata)
        return data

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), sort_keys=False, allow_unicode=True)


class RuleDSLParser:
    """Responsável por ler e validar YAML do editor de regras."""

    def parse(self, yaml_text: str) -> RuleDocument:
        try:
            payload = yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError as exc:  # pragma: no cover - erro de parser externo
            raise RuleDSLParseError(str(exc)) from exc

        if isinstance(payload, list):
            rules_source = payload
            metadata: dict[str, Any] = {}
            name: str | None = None
            version: str | None = None
        elif isinstance(payload, dict):
            metadata = self._extract_metadata(payload)
            name = self._optional_str(payload.get("name"))
            version = self._optional_str(payload.get("version"))
            rules_source = payload.get("rules")
            if rules_source is None:
                raise RuleDSLValidationError("Documento YAML deve conter a chave 'rules'.")
        else:
            raise RuleDSLValidationError("YAML raiz deve ser um objeto ou lista de regras.")

        if not isinstance(rules_source, list):
            raise RuleDSLValidationError("A chave 'rules' deve ser uma lista.")

        rules: list[RuleDefinition] = [self._parse_rule(rule, index) for index, rule in enumerate(rules_source, start=1)]
        return RuleDocument(name=name, version=version, metadata=metadata, rules=rules)

    def materialize(self, payload: dict[str, Any]) -> RuleDocument:
        yaml_text = payload.get("yaml") if isinstance(payload, dict) else None
        if yaml_text:
            return self.parse(yaml_text)

        rules_data = payload.get("rules") if isinstance(payload, dict) else None
        if not isinstance(rules_data, list):
            return RuleDocument()

        rules = []
        for index, rule in enumerate(rules_data, start=1):
            if not isinstance(rule, dict):
                raise RuleDSLValidationError(
                    f"Regra na posição {index} deve ser um objeto."
                )
            rules.append(self._parse_rule(rule, index))
        name = self._optional_str(payload.get("name")) if isinstance(payload, dict) else None
        version = self._optional_str(payload.get("version")) if isinstance(payload, dict) else None
        metadata = self._extract_metadata(payload if isinstance(payload, dict) else {})
        return RuleDocument(name=name, version=version, metadata=metadata, rules=rules)

    def _parse_rule(self, data: Any, position: int) -> RuleDefinition:
        if not isinstance(data, dict):
            raise RuleDSLValidationError(f"Regra na posição {position} deve ser um objeto.")

        rule_id = self._require_str(data.get("id"), f"Regra {position} precisa do campo 'id'.")
        name = self._require_str(
            data.get("name"), f"Regra {rule_id} precisa do campo 'name'."
        )
        description = self._optional_str(data.get("description"))
        scope = self._optional_str(data.get("scope")) or "invoice"
        if scope not in {"invoice", "item"}:
            raise RuleDSLValidationError(
                f"Regra {rule_id}: campo 'scope' deve ser 'invoice' ou 'item'."
            )

        when = self._normalize_conditions(data.get("when"), rule_id)
        then = self._normalize_then(data.get("then"), rule_id)
        disabled = bool(data.get("disabled", False))

        return RuleDefinition(
            id=rule_id,
            name=name,
            scope=scope,
            description=description,
            when=when,
            then=then,
            disabled=disabled,
        )

    def _normalize_conditions(self, payload: Any, rule_id: str) -> dict[str, Any]:
        if payload is None:
            return {}
        if isinstance(payload, str):
            return {"all": [payload]}
        if not isinstance(payload, dict):
            raise RuleDSLValidationError(
                f"Regra {rule_id}: campo 'when' deve ser string ou objeto com 'all'/'any'."
            )

        normalized: dict[str, Any] = {}
        if "all" in payload:
            normalized["all"] = self._normalize_clauses(payload["all"], rule_id, "all")
        if "any" in payload:
            normalized["any"] = self._normalize_clauses(payload["any"], rule_id, "any")
        if "not" in payload:
            normalized["not"] = self._normalize_conditions(payload["not"], rule_id)
        return normalized

    def _normalize_clauses(
        self, payload: Any, rule_id: str, key: str
    ) -> list[str | dict[str, Any]]:
        if isinstance(payload, str):
            return [payload]
        if not isinstance(payload, list):
            raise RuleDSLValidationError(
                f"Regra {rule_id}: bloco '{key}' deve ser uma lista de expressões."
            )
        clauses: list[str | dict[str, Any]] = []
        for clause in payload:
            if isinstance(clause, str):
                clauses.append(clause)
            elif isinstance(clause, dict):
                clauses.append(self._normalize_conditions(clause, rule_id))
            else:
                raise RuleDSLValidationError(
                    f"Regra {rule_id}: cláusulas em '{key}' devem ser strings ou objetos."
                )
        return clauses

    def _normalize_then(self, payload: Any, rule_id: str) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise RuleDSLValidationError(
                f"Regra {rule_id}: campo 'then' deve ser um objeto com a ação."
            )

        inconsistency = self._require_str(
            payload.get("inconsistency_code"),
            f"Regra {rule_id}: 'then.inconsistency_code' é obrigatório.",
        )
        severity = self._require_str(
            payload.get("severity"), f"Regra {rule_id}: 'then.severity' é obrigatório."
        )
        message = self._require_str(
            payload.get("message_pt"), f"Regra {rule_id}: 'then.message_pt' é obrigatório."
        )

        normalized: dict[str, Any] = {
            "inconsistency_code": inconsistency,
            "severity": severity,
            "message_pt": message,
        }

        if payload.get("suggestion_code"):
            normalized["suggestion_code"] = self._require_str(
                payload.get("suggestion_code"),
                f"Regra {rule_id}: 'then.suggestion_code' deve ser string.",
            )
        if payload.get("references"):
            references = payload.get("references")
            if not isinstance(references, list) or not all(isinstance(ref, str) for ref in references):
                raise RuleDSLValidationError(
                    f"Regra {rule_id}: 'then.references' deve ser lista de strings."
                )
            normalized["references"] = list(references)
        if payload.get("evidence"):
            evidence = payload.get("evidence")
            if not isinstance(evidence, dict):
                raise RuleDSLValidationError(
                    f"Regra {rule_id}: 'then.evidence' deve ser um objeto."
                )
            normalized["evidence"] = {str(k): v for k, v in evidence.items()}
        return normalized

    def _extract_metadata(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw_metadata = payload.get("metadata") if isinstance(payload, dict) else None
        if raw_metadata is None:
            return {}
        if not isinstance(raw_metadata, dict):
            raise RuleDSLValidationError("Campo 'metadata' deve ser um objeto.")
        return deepcopy(raw_metadata)

    def _require_str(self, value: Any, error: str) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip()
        raise RuleDSLValidationError(error)

    def _optional_str(self, value: Any) -> str | None:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return None


class RuleComposer:
    """Aplica overrides sobre o baseline global."""

    def compose(
        self, baseline: Iterable[RuleDefinition], overrides: Iterable[RuleDefinition]
    ) -> list[RuleDefinition]:
        result: dict[str, RuleDefinition] = {}
        for rule in baseline:
            if not rule.disabled:
                result[rule.id] = rule.copy()

        for rule in overrides:
            if rule.disabled:
                result.pop(rule.id, None)
                continue
            result[rule.id] = rule.copy()

        return list(result.values())
