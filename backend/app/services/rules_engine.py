from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass
class RuleResult:
    rule_id: str
    inconsistency_code: str
    severity: str
    message_pt: str
    suggestion_code: str | None = None
    references: list[str] | None = None


class RuleEngine:
    def __init__(self, rules: Iterable[dict[str, Any]]):
        self.rules = list(rules)

    def evaluate(self, context: dict[str, Any]) -> list[RuleResult]:
        results: list[RuleResult] = []
        for rule in self.rules:
            if rule.get("when"):
                results.append(
                    RuleResult(
                        rule_id=rule["id"],
                        inconsistency_code=rule["then"].get("inconsistency_code", ""),
                        severity=rule["then"].get("severity", "medium"),
                        message_pt=rule["then"].get("message_pt", ""),
                        suggestion_code=rule["then"].get("suggestion_code"),
                        references=rule["then"].get("references"),
                    )
                )
        return results
