from app.services.rules_engine import RuleEngine


def test_rule_engine_returns_results() -> None:
    rules = [
        {
            "id": "TEST-1",
            "when": {"all": ["item.total_value > 0"]},
            "then": {
                "inconsistency_code": "CODE",
                "severity": "high",
                "message_pt": "Mensagem",
                "suggestion_code": "SUG",
            },
        }
    ]
    engine = RuleEngine(rules)
    results = engine.evaluate({"item": {"total_value": 100}})
    assert len(results) == 1
    assert results[0].rule_id == "TEST-1"
