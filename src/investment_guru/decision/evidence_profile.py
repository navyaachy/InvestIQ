from __future__ import annotations

from typing import Any


FACTOR_LABELS = {
    "market_behaviour": "Price Behaviour",
    "risk": "Risk",
    "fundamentals": "Fundamentals",
    "growth": "Growth",
    "valuation": "Valuation",
}


def classify_evidence(score: float | None) -> str:
    """
    Convert an analytical score into a descriptive evidence rating.

    This is intentionally not presented as a recommendation
    or investment score.
    """

    if score is None:
        return "Not enough data"

    if score >= 75:
        return "Strong"

    if score >= 60:
        return "Supportive"

    if score >= 40:
        return "Mixed"

    return "Weak"


def build_reason(
    factor: str,
    score: float | None,
) -> str:

    if score is None:
        return "Evidence for this dimension is currently unavailable."

    if factor == "market_behaviour":

        if score >= 75:
            return "Recent price behaviour provides relatively strong evidence."
        if score >= 60:
            return "Recent price behaviour provides supportive evidence."
        if score >= 40:
            return "Recent price behaviour is mixed."
        return "Recent price behaviour provides weaker evidence."

    if factor == "risk":

        if score >= 75:
            return "Risk indicators are relatively supportive."
        if score >= 60:
            return "Risk indicators are broadly manageable within the available evidence."
        if score >= 40:
            return "Risk indicators show a mixed profile."
        return "Risk indicators require attention."

    if factor == "fundamentals":

        if score >= 75:
            return "Available fundamental indicators provide strong evidence."
        if score >= 60:
            return "Available fundamental indicators provide supportive evidence."
        if score >= 40:
            return "Fundamental evidence is mixed."
        return "Fundamental evidence is currently weaker."

    if factor == "growth":

        if score >= 75:
            return "Available growth indicators provide strong evidence."
        if score >= 60:
            return "Available growth indicators provide supportive evidence."
        if score >= 40:
            return "Growth evidence is mixed."
        return "Growth evidence is currently weaker."

    if factor == "valuation":

        if score >= 75:
            return "Available valuation evidence is relatively stronger."
        if score >= 60:
            return "Available valuation evidence is supportive."
        if score >= 40:
            return "Valuation evidence is mixed."
        return "Valuation evidence requires attention."

    return "Evidence is available for this dimension."


def build_evidence_profile(
    scores: dict[str, float | None],
) -> dict[str, Any]:

    dimensions = []

    for factor, label in FACTOR_LABELS.items():

        score = scores.get(factor)

        dimensions.append(
            {
                "factor": factor,
                "label": label,
                "rating": classify_evidence(score),
                "reason": build_reason(
                    factor=factor,
                    score=score,
                ),
                "available": score is not None,
            }
        )

    available_count = sum(
        1
        for item in dimensions
        if item["available"]
    )

    total_count = len(dimensions)

    completeness = (
        (available_count / total_count) * 100
        if total_count
        else 0
    )

    return {
        "dimensions": dimensions,
        "available_dimensions": available_count,
        "total_dimensions": total_count,
        "completeness": round(completeness, 2),
    }