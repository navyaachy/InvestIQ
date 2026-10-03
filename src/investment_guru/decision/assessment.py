from __future__ import annotations


HORIZON_WEIGHTS = {
    "short-term": {
        "market_behaviour": 0.30,
        "risk": 0.25,
        "fundamentals": 0.10,
        "growth": 0.10,
        "valuation": 0.15,
        "portfolio_fit": 0.10,
    },
    "medium-term": {
        "market_behaviour": 0.15,
        "risk": 0.20,
        "fundamentals": 0.20,
        "growth": 0.15,
        "valuation": 0.20,
        "portfolio_fit": 0.10,
    },
    "long-term": {
        "market_behaviour": 0.05,
        "risk": 0.15,
        "fundamentals": 0.25,
        "growth": 0.20,
        "valuation": 0.25,
        "portfolio_fit": 0.10,
    },
}


def get_horizon_weights(horizon: str) -> dict[str, float]:
    """Return factor weights for the selected investment horizon."""

    horizon = horizon.strip().lower()

    if horizon not in HORIZON_WEIGHTS:
        raise ValueError(
            "Horizon must be short-term, medium-term, or long-term."
        )

    return HORIZON_WEIGHTS[horizon].copy()


def calculate_overall_score(
    scores: dict[str, float],
    weights: dict[str, float],
) -> float:
    """Calculate a weighted score using available factors only."""

    available_factors = [
        factor
        for factor in weights
        if factor in scores
    ]

    if not available_factors:
        raise ValueError("No scored factors are available.")

    available_weight = sum(
        weights[factor]
        for factor in available_factors
    )

    weighted_score = sum(
        scores[factor] * weights[factor]
        for factor in available_factors
    )

    return round(
        weighted_score / available_weight,
        2,
    )


def calculate_coverage(
    scores: dict[str, float],
    weights: dict[str, float],
) -> float:
    """Calculate the percentage of the framework supported by data."""

    total_weight = sum(weights.values())

    available_weight = sum(
        weights[factor]
        for factor in weights
        if factor in scores
    )

    if total_weight == 0:
        return 0.0

    return round(
        (available_weight / total_weight) * 100,
        2,
    )


def classify_assessment(score: float) -> str:
    """Convert score into a neutral assessment band."""

    if score >= 75:
        return "Strong profile"

    if score >= 60:
        return "Moderately strong profile"

    if score >= 40:
        return "Mixed profile"

    return "Weaker profile"


def classify_evidence(coverage: float) -> str:
    """Describe how complete the available evidence is."""

    if coverage >= 80:
        return "High"

    if coverage >= 60:
        return "Moderate"

    if coverage >= 40:
        return "Limited"

    return "Very limited"


def build_assessment(
    scores: dict[str, float],
    horizon: str = "long-term",
) -> dict:
    """Build an explainable investment assessment."""

    weights = get_horizon_weights(horizon)

    overall_score = calculate_overall_score(
        scores=scores,
        weights=weights,
    )

    coverage = calculate_coverage(
        scores=scores,
        weights=weights,
    )

    evidence_level = classify_evidence(coverage)

    factors = []

    for factor, weight in weights.items():

        score = scores.get(factor)

        if score is None:
            continue

        contribution = round(
            score * weight,
            2,
        )

        factors.append(
            {
                "factor": factor,
                "score": round(score, 2),
                "weight": weight,
                "contribution": contribution,
            }
        )

    factors.sort(
        key=lambda item: item["contribution"],
        reverse=True,
    )

    return {
        "horizon": horizon,
        "overall_score": overall_score,
        "coverage": coverage,
        "evidence_level": evidence_level,
        "assessment": classify_assessment(overall_score),
        "scores": scores,
        "weights": weights,
        "factors": factors,
    }