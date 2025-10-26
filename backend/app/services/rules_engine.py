from __future__ import annotations

import ast
import math
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable, Mapping

from app.services.rules_dsl import RuleDefinition


class RuleEvaluationError(ValueError):
    """Erro lançado quando uma expressão da DSL não pode ser avaliada."""


@dataclass(slots=True)
class RuleResult:
    rule_id: str
    name: str
    inconsistency_code: str
    severity: str
    message_pt: str
    suggestion_code: str | None = None
    references: list[str] | None = None
    evidence: dict[str, Any] | None = None
    item: Any | None = None


class RuleHelper:
    """Funções auxiliares disponíveis para expressões."""

    def __init__(self, invoice: Any, items: list[Any]) -> None:
        self.invoice = invoice
        self.items = items

    def items_sum(self, attr: str) -> float:
        total = 0.0
        for item in self.items:
            value = getattr(item, attr, 0) or 0
            total += float(value)
        return total

    def total_variance(self) -> float:
        items_total = self.items_sum("total_value")
        freight = float(getattr(self.invoice, "freight_value", 0) or 0)
        invoice_total = float(getattr(self.invoice, "total_value", 0) or 0)
        return abs((items_total + freight) - invoice_total)

    def count_items(self) -> int:
        return len(self.items)

    def value_or(self, value: Any, default: float = 0.0) -> float:
        return float(value) if value is not None else float(default)


class ExpressionEvaluator:
    allowed_builtins: Mapping[str, Any] = {
        "len": len,
        "min": min,
        "max": max,
        "abs": abs,
        "sum": sum,
        "float": float,
        "int": int,
        "str": str,
        "round": round,
        "math": math,
    }

    _BOOLEAN_RE = re.compile(r"\b(true|false|null)\b", re.IGNORECASE)

    def __init__(self, context: Mapping[str, Any]):
        self.context = context

    def evaluate(self, expression: str) -> Any:
        normalized = self._normalize(expression)
        try:
            tree = ast.parse(normalized, mode="eval")
        except SyntaxError as exc:  # pragma: no cover - erro sintático evidente
            raise RuleEvaluationError(str(exc)) from exc
        return self._eval_node(tree.body)

    def _normalize(self, expression: str) -> str:
        def replace(match: re.Match[str]) -> str:
            token = match.group(1).lower()
            return {"true": "True", "false": "False", "null": "None"}[token]

        return self._BOOLEAN_RE.sub(replace, expression)

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.BoolOp):
            values = [self._eval_node(value) for value in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
            raise RuleEvaluationError("Operador booleano não suportado")
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self._apply_binop(node.op, left, right)
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.Not):
                return not operand
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            raise RuleEvaluationError("Operador unário não suportado")
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                if not self._apply_compare(op, left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Call):
            func = self._eval_node(node.func)
            if not callable(func):
                raise RuleEvaluationError("Chamada de função inválida")
            args = [self._eval_node(arg) for arg in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords}
            return func(*args, **kwargs)
        if isinstance(node, ast.Name):
            if node.id in self.context:
                return self.context[node.id]
            if node.id in self.allowed_builtins:
                return self.allowed_builtins[node.id]
            raise RuleEvaluationError(f"Variável '{node.id}' não disponível no contexto")
        if isinstance(node, ast.Attribute):
            value = self._eval_node(node.value)
            if node.attr.startswith("_"):
                raise RuleEvaluationError("Acesso a atributos privados não permitido")
            return getattr(value, node.attr)
        if isinstance(node, ast.Subscript):
            value = self._eval_node(node.value)
            key = self._eval_node(node.slice)
            return value[key]
        if isinstance(node, ast.Slice):
            lower = self._eval_node(node.lower) if node.lower else None
            upper = self._eval_node(node.upper) if node.upper else None
            step = self._eval_node(node.step) if node.step else None
            return slice(lower, upper, step)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.List):
            return [self._eval_node(element) for element in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self._eval_node(element) for element in node.elts)
        if isinstance(node, ast.Dict):
            return {
                self._eval_node(key): self._eval_node(value)
                for key, value in zip(node.keys, node.values)
            }
        raise RuleEvaluationError(f"Expressão não suportada: {ast.dump(node)}")

    def _apply_binop(self, op: ast.operator, left: Any, right: Any) -> Any:
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            return left / right
        if isinstance(op, ast.Mod):
            return left % right
        raise RuleEvaluationError("Operador matemático não suportado")

    def _apply_compare(self, op: ast.cmpop, left: Any, right: Any) -> bool:
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.NotEq):
            return left != right
        if isinstance(op, ast.Gt):
            return left > right
        if isinstance(op, ast.GtE):
            return left >= right
        if isinstance(op, ast.Lt):
            return left < right
        if isinstance(op, ast.LtE):
            return left <= right
        if isinstance(op, ast.In):
            return left in right
        if isinstance(op, ast.NotIn):
            return left not in right
        if isinstance(op, ast.Is):
            return left is right
        if isinstance(op, ast.IsNot):
            return left is not right
        raise RuleEvaluationError("Operador de comparação não suportado")


class RuleEngine:
    def __init__(self, rules: Iterable[RuleDefinition]):
        self.rules = [rule for rule in rules if not rule.disabled]

    def evaluate(self, *, invoice: Any, items: Iterable[Any] | None = None) -> list[RuleResult]:
        invoice_items = list(items or getattr(invoice, "items", []) or [])
        helper = RuleHelper(invoice, invoice_items)
        results: list[RuleResult] = []

        for rule in self.rules:
            if rule.scope == "item":
                for item in invoice_items:
                    context = {"invoice": invoice, "item": item, "helpers": helper}
                    if self._matches(rule.when, context):
                        results.append(self._build_result(rule, context, item))
            else:
                context = {"invoice": invoice, "helpers": helper}
                if self._matches(rule.when, context):
                    results.append(self._build_result(rule, context, None))
        return results

    def _matches(self, condition: dict[str, Any], context: Mapping[str, Any]) -> bool:
        if not condition:
            return True

        if "all" in condition:
            for clause in condition["all"]:
                if not self._evaluate_clause(clause, context):
                    return False

        if "any" in condition:
            any_clauses = condition["any"]
            if any_clauses and not any(
                self._evaluate_clause(clause, context) for clause in any_clauses
            ):
                return False

        if "not" in condition and self._matches(condition["not"], context):
            return False

        return True

    def _evaluate_clause(self, clause: Any, context: Mapping[str, Any]) -> bool:
        if isinstance(clause, str):
            result = ExpressionEvaluator(context).evaluate(clause)
            return bool(result)
        if isinstance(clause, dict):
            return self._matches(clause, context)
        raise RuleEvaluationError("Cláusula de condição inválida")

    def _build_result(
        self, rule: RuleDefinition, context: Mapping[str, Any], item: Any | None
    ) -> RuleResult:
        then = rule.then
        evidence_payload = then.get("evidence") or {}
        evidence: dict[str, Any] | None = None
        if evidence_payload:
            evidence = {}
            for key, value in evidence_payload.items():
                if isinstance(value, str):
                    evaluated = ExpressionEvaluator(context).evaluate(value)
                else:
                    evaluated = value
                evidence[key] = self._serialize_value(evaluated)

        references = then.get("references")
        if references:
            references = list(references)

        return RuleResult(
            rule_id=rule.id,
            name=rule.name,
            inconsistency_code=then["inconsistency_code"],
            severity=then["severity"],
            message_pt=then["message_pt"],
            suggestion_code=then.get("suggestion_code"),
            references=references,
            evidence=evidence,
            item=item,
        )

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, Decimal):
            return float(value)
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:  # pragma: no cover - objetos não compatíveis
                pass
        return repr(value)
