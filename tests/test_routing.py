from graph import evaluate_customer, route_action


def evaluated(action: str, confidence: float):
    return {"proposed_action": action, "confidence_score": confidence}


def test_policy_override_precedes_confidence():
    assert route_action(evaluated("increase_credit_limit", 0.99))["route"] == "execute_high_risk_action"


def test_high_confidence_low_risk_auto_executes():
    assert route_action(evaluated("send_email", 0.90))["route"] == "execute_low_risk_action"


def test_low_confidence_escalates():
    assert route_action(evaluated("send_email", 0.82))["route"] == "execute_high_risk_action"


def test_reasoning_is_data_driven_and_confidence_bounded():
    for income, churn in [(25_000_000, 0.2), (2_000_000, 0.2), (60_000_000, 0.9)]:
        result = evaluate_customer({"total_operating_income": income, "churn_probability": churn})
        assert 0.0 <= result["confidence_score"] <= 1.0
        assert result["proposed_action"] in {"send_email", "increase_credit_limit"}
