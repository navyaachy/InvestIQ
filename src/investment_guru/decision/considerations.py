from __future__ import annotations


FACTOR_LABELS = {
    "market_behaviour": "Market Behaviour",
    "risk": "Risk",
    "fundamentals": "Fundamentals",
    "growth": "Growth",
    "valuation": "Valuation",
    "portfolio_fit": "Portfolio Fit",
}


def _label(factor: str) -> str:
    return FACTOR_LABELS.get(
        factor,
        factor.replace("_", " ").title(),
    )


def _get_consideration(
    factor: str,
    score: float,
) -> str:
    """
    Generate a decision consideration based on
    the current evidence score.

    These are investigation prompts, not buy/sell
    recommendations.
    """

    label = _label(factor)

    if factor == "market_behaviour":

        if score < 40:
            return (
                f"{label} is relatively weak at "
                f"{score:.1f}/100. Review recent price "
                f"performance, volatility, drawdown and "
                f"benchmark-relative behaviour."
            )

        if score < 60:
            return (
                f"{label} is mixed at "
                f"{score:.1f}/100. Review whether recent "
                f"price behaviour is consistent with the "
                f"intended investment horizon."
            )

        return (
            f"{label} is relatively strong at "
            f"{score:.1f}/100. Continue monitoring recent "
            f"market behaviour against the benchmark."
        )

    if factor == "risk":

        if score < 40:
            return (
                f"{label} evidence is relatively weak at "
                f"{score:.1f}/100. Pay particular attention "
                f"to volatility, drawdown and risk-adjusted "
                f"performance."
            )

        if score < 60:
            return (
                f"{label} is mixed at "
                f"{score:.1f}/100. Review whether the "
                f"observed risk characteristics fit the "
                f"investor's tolerance."
            )

        return (
            f"{label} evidence is relatively strong at "
            f"{score:.1f}/100 within the current framework. "
            f"Continue monitoring changes in risk metrics."
        )

    if factor == "fundamentals":

        if score < 40:
            return (
                f"{label} is relatively weak at "
                f"{score:.1f}/100. Review profitability, "
                f"leverage, earnings and other available "
                f"financial indicators."
            )

        if score < 60:
            return (
                f"{label} is mixed at "
                f"{score:.1f}/100. Review the company's "
                f"financial strength and the direction of "
                f"its underlying fundamentals."
            )

        return (
            f"{label} provides relatively stronger "
            f"evidence at {score:.1f}/100. Continue "
            f"monitoring changes in the company's "
            f"financial metrics."
        )

    if factor == "growth":

        if score < 40:
            return (
                f"{label} is relatively weak at "
                f"{score:.1f}/100. Examine revenue, earnings "
                f"and other available growth indicators "
                f"before relying on the current assessment."
            )

        if score < 60:
            return (
                f"{label} is mixed at "
                f"{score:.1f}/100. Compare the available "
                f"growth evidence with the current valuation."
            )

        return (
            f"{label} is relatively strong at "
            f"{score:.1f}/100. Check whether the observed "
            f"growth remains consistent with the current "
            f"valuation."
        )

    if factor == "valuation":

        if score < 40:
            return (
                f"{label} is relatively weak at "
                f"{score:.1f}/100. Review the valuation "
                f"multiples and compare them with relevant "
                f"historical or peer context."
            )

        if score < 60:
            return (
                f"{label} is mixed at "
                f"{score:.1f}/100. Examine valuation alongside "
                f"fundamentals and growth rather than in "
                f"isolation."
            )

        return (
            f"{label} is relatively strong at "
            f"{score:.1f}/100 within the current valuation "
            f"framework. Reassess if earnings expectations "
            f"or market multiples change."
        )

    if factor == "portfolio_fit":

        if score < 40:
            return (
                f"{label} is relatively weak at "
                f"{score:.1f}/100. Review risk tolerance, "
                f"existing exposure and investment horizon "
                f"before considering additional exposure."
            )

        if score < 60:
            return (
                f"{label} is mixed at "
                f"{score:.1f}/100. Review how the position "
                f"fits the investor's risk tolerance, horizon "
                f"and existing exposure."
            )

        return (
            f"{label} is relatively strong at "
            f"{score:.1f}/100 under the current portfolio "
            f"inputs. Reassess if portfolio exposure or "
            f"investor circumstances change."
        )

    return (
        f"{label} currently has a score of "
        f"{score:.1f}/100. Review the underlying evidence "
        f"before relying on this factor."
    )


def build_decision_considerations(
    scores: dict[str, float],
) -> dict:
    """
    Build evidence-based considerations for the investor.

    This module does not produce buy, sell, hold or
    price-target recommendations.
    """

    available_scores = {
        factor: float(score)
        for factor, score in scores.items()
        if score is not None
    }

    if not available_scores:
        return {
            "key_considerations": [],
            "strongest_evidence": [],
            "areas_to_review": [],
        }

    strongest = sorted(
        available_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    weakest = sorted(
        available_scores.items(),
        key=lambda item: item[1],
    )

    strongest_evidence = [
        {
            "factor": _label(factor),
            "score": round(score, 2),
        }
        for factor, score in strongest[:3]
    ]

    areas_to_review = [
        {
            "factor": _label(factor),
            "score": round(score, 2),
        }
        for factor, score in weakest[:3]
    ]

    considerations = [
        {
            "factor": _label(factor),
            "score": round(score, 2),
            "text": _get_consideration(
                factor,
                score,
            ),
        }
        for factor, score in weakest[:4]
    ]

    return {
        "key_considerations": considerations,
        "strongest_evidence": strongest_evidence,
        "areas_to_review": areas_to_review,
    }