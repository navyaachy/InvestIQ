import pytest

from src.investment_guru.analytics.portfolio import (
    calculate_holding_values,
    calculate_portfolio_summary,
)
from src.investment_guru.decision.assessment import (
    calculate_overall_score,
    calculate_coverage,
    classify_assessment,
    classify_evidence,
)
from src.investment_guru.data.data_freshness import (
    classify_data_freshness,
)


def test_holding_values_calculation():
    result = calculate_holding_values(
        ticker="reliance.ns",
        quantity=10,
        buy_price=1400,
        current_price=1200,
    )

    assert result["Ticker"] == "RELIANCE.NS"
    assert result["Invested Value"] == 14000
    assert result["Current Value"] == 12000
    assert result["P&L"] == -2000
    assert result["Return %"] == pytest.approx(-14.2857, rel=1e-3)


def test_portfolio_summary():
    holdings = [
        {
            "Ticker": "RELIANCE.NS",
            "Quantity": 10,
            "Buy Price": 1400,
            "Current Price": 1200,
        },
        {
            "Ticker": "TCS.NS",
            "Quantity": 5,
            "Buy Price": 3000,
            "Current Price": 3200,
        },
    ]

    result = calculate_portfolio_summary(holdings)

    assert result["holding_count"] == 2
    assert result["invested_value"] == 29000
    assert result["current_value"] == 28000
    assert result["pnl"] == -1000
    assert result["return_pct"] == pytest.approx(-3.4483, rel=1e-3)


def test_invalid_holdings_are_ignored():
    holdings = [
        {
            "Ticker": "RELIANCE.NS",
            "Quantity": 0,
            "Buy Price": 1400,
            "Current Price": 1200,
        },
        {
            "Ticker": "",
            "Quantity": 10,
            "Buy Price": 1400,
            "Current Price": 1200,
        },
        {
            "Ticker": "TCS.NS",
            "Quantity": 5,
            "Buy Price": 3000,
            "Current Price": 3200,
        },
    ]

    result = calculate_portfolio_summary(holdings)

    assert result["holding_count"] == 1
    assert result["holdings"][0]["Ticker"] == "TCS.NS"


def test_zero_invested_value_does_not_crash():
    result = calculate_holding_values(
        ticker="TEST.NS",
        quantity=0,
        buy_price=0,
        current_price=100,
    )

    assert result["Invested Value"] == 0
    assert result["Current Value"] == 0
    assert result["Return %"] is None


def test_assessment_score_uses_available_weights():
    scores = {
        "fundamentals": 80,
        "valuation": 60,
    }

    weights = {
        "fundamentals": 0.5,
        "valuation": 0.5,
        "growth": 0.2,
    }

    result = calculate_overall_score(scores, weights)

    assert result == pytest.approx(70.0)


def test_assessment_coverage():
    scores = {
        "fundamentals": 80,
        "valuation": 60,
    }

    weights = {
        "fundamentals": 0.5,
        "valuation": 0.3,
        "growth": 0.2,
    }

    result = calculate_coverage(scores, weights)

    assert result == pytest.approx(80.0)


def test_assessment_classification_boundaries():
    assert classify_assessment(80) == "Strong profile"
    assert classify_assessment(60) == "Moderately strong profile"
    assert classify_assessment(40) == "Mixed profile"
    assert classify_assessment(20) == "Weaker profile"


def test_evidence_classification():
    assert classify_evidence(90) == "High"
    assert classify_evidence(70) == "Moderate"
    assert classify_evidence(50) == "Limited"
    assert classify_evidence(20) == "Very limited"


def test_missing_freshness_timestamp():
    result = classify_data_freshness(None)

    assert result["status"] == "Unavailable"
    assert result["age_minutes"] is None


def test_invalid_freshness_timestamp():
    result = classify_data_freshness("not-a-timestamp")

    assert result["status"] == "Unavailable"
    assert result["age_minutes"] is None

def test_positive_holding_return():
    result = calculate_holding_values(
        ticker="TCS.NS",
        quantity=5,
        buy_price=3000,
        current_price=3600,
    )

    assert result["Invested Value"] == 15000
    assert result["Current Value"] == 18000
    assert result["P&L"] == 3000
    assert result["Return %"] == pytest.approx(20.0)


def test_freshness_outside_market_hours():
    result = classify_data_freshness(
        "2026-10-03T20:37:11+00:00"
    )

    assert result["status"] in {
        "Latest available",
        "Fresh",
        "Aging",
        "Potentially stale",
    }
    assert result["age_minutes"] is not None


def test_freshness_result_has_required_fields():
    result = classify_data_freshness(None)

    assert "status" in result
    assert "label" in result
    assert "age_minutes" in result
    assert "message" in result


def test_assessment_score_changes_with_weights():
    scores = {
        "fundamentals": 90,
        "valuation": 30,
    }

    weights = {
        "fundamentals": 0.8,
        "valuation": 0.2,
    }

    result = calculate_overall_score(scores, weights)

    assert result == pytest.approx(78.0)

