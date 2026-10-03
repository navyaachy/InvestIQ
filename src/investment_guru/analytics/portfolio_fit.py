from __future__ import annotations

from typing import Any


RISK_TOLERANCE_LEVELS = {
    "conservative": 1,
    "moderate": 2,
    "aggressive": 3,
}


HORIZON_LEVELS = {
    "short-term": 1,
    "medium-term": 2,
    "long-term": 3,
}


def _risk_fit_score(
    risk_score: float | None,
    risk_tolerance: str,
) -> float | None:
    """
    Estimate compatibility between the stock's risk profile
    and the investor's stated risk tolerance.

    risk_score:
        0   = weaker risk profile
        100 = stronger risk profile / lower observed risk
    """

    if risk_score is None:
        return None

    tolerance = risk_tolerance.strip().lower()

    if tolerance not in RISK_TOLERANCE_LEVELS:
        raise ValueError(
            "Risk tolerance must be conservative, moderate, or aggressive."
        )

    if tolerance == "conservative":

        if risk_score >= 70:
            return 100.0

        if risk_score >= 50:
            return 70.0

        if risk_score >= 30:
            return 40.0

        return 10.0

    if tolerance == "moderate":

        if risk_score >= 70:
            return 85.0

        if risk_score >= 50:
            return 100.0

        if risk_score >= 30:
            return 60.0

        return 30.0

    # Aggressive

    if risk_score >= 70:
        return 70.0

    if risk_score >= 50:
        return 85.0

    if risk_score >= 30:
        return 100.0

    return 80.0


def _horizon_fit_score(
    investor_horizon: str,
    stock_horizon: str,
) -> float:
    """
    Compare the investor's intended horizon with the
    horizon classification assigned to the stock.

    Same horizon:
        100

    One level apart:
        70

    Two levels apart:
        40
    """

    investor_horizon = investor_horizon.strip().lower()
    stock_horizon = stock_horizon.strip().lower()

    if investor_horizon not in HORIZON_LEVELS:
        raise ValueError(
            "Investor horizon must be short-term, medium-term, or long-term."
        )

    if stock_horizon not in HORIZON_LEVELS:
        raise ValueError(
            "Stock horizon must be short-term, medium-term, or long-term."
        )

    difference = abs(
        HORIZON_LEVELS[investor_horizon]
        - HORIZON_LEVELS[stock_horizon]
    )

    if difference == 0:
        return 100.0

    if difference == 1:
        return 70.0

    return 40.0


def _exposure_fit_score(
    existing_exposure: float | None,
) -> float | None:
    """
    Score existing exposure to the stock.

    Lower existing exposure receives a higher
    diversification-fit score.

    This is a transparent heuristic and is not
    an asset-allocation recommendation.
    """

    if existing_exposure is None:
        return None

    if existing_exposure < 0:
        return None

    if existing_exposure <= 5:
        return 100.0

    if existing_exposure <= 10:
        return 80.0

    if existing_exposure <= 20:
        return 60.0

    if existing_exposure <= 30:
        return 35.0

    return 10.0


def calculate_portfolio_fit(
    risk_score: float | None,
    risk_tolerance: str,
    investor_horizon: str,
    stock_horizon: str,
    investment_amount: float | None = None,
    existing_exposure: float | None = None,
) -> dict[str, Any]:
    """
    Calculate an explainable Portfolio Fit score.

    Components:

        Risk compatibility       50%
        Exposure compatibility   30%
        Horizon compatibility    20%

    Investment amount is collected for context but is not
    scored because portfolio-level financial information
    is required to determine whether an absolute amount
    is appropriate.
    """

    risk_fit = _risk_fit_score(
        risk_score=risk_score,
        risk_tolerance=risk_tolerance,
    )

    horizon_fit = _horizon_fit_score(
        investor_horizon=investor_horizon,
        stock_horizon=stock_horizon,
    )

    exposure_fit = _exposure_fit_score(
        existing_exposure=existing_exposure,
    )

    component_scores = {
        "risk_fit": risk_fit,
        "exposure_fit": exposure_fit,
        "horizon_fit": horizon_fit,
    }

    component_weights = {
        "risk_fit": 0.50,
        "exposure_fit": 0.30,
        "horizon_fit": 0.20,
    }

    available_components = [
        component
        for component in component_weights
        if component_scores[component] is not None
    ]

    if available_components:

        available_weight = sum(
            component_weights[component]
            for component in available_components
        )

        weighted_score = sum(
            component_scores[component]
            * component_weights[component]
            for component in available_components
        )

        overall_score = (
            weighted_score
            / available_weight
        )

    else:
        overall_score = None

    coverage = (
        len(available_components)
        / len(component_weights)
        * 100
    )

    if overall_score is None:

        assessment = "Portfolio fit unavailable"

    elif overall_score >= 75:

        assessment = "Strong portfolio fit"

    elif overall_score >= 50:

        assessment = "Moderate portfolio fit"

    else:

        assessment = "Limited portfolio fit"

    return {
        "overall_score": (
            round(overall_score, 2)
            if overall_score is not None
            else None
        ),

        "coverage": round(
            coverage,
            2,
        ),

        "assessment": assessment,

        "components": {
            "risk_fit": (
                round(risk_fit, 2)
                if risk_fit is not None
                else None
            ),

            "exposure_fit": (
                round(exposure_fit, 2)
                if exposure_fit is not None
                else None
            ),

            "horizon_fit": (
                round(horizon_fit, 2)
                if horizon_fit is not None
                else None
            ),
        },

        "weights": component_weights,

        "inputs": {
            "risk_tolerance": risk_tolerance,
            "investor_horizon": investor_horizon,
            "stock_horizon": stock_horizon,
            "investment_amount": investment_amount,
            "existing_exposure": existing_exposure,
        },
    }