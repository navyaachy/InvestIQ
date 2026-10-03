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


def _describe_score(score: float) -> str:

    if score >= 75:
        return "strong"

    if score >= 60:
        return "moderately strong"

    if score >= 40:
        return "mixed"

    return "weak"


def _positive_factors(
    scores: dict[str, float],
) -> list[tuple[str, float]]:

    return sorted(
        [
            (factor, score)
            for factor, score in scores.items()
            if score >= 60
        ],
        key=lambda item: item[1],
        reverse=True,
    )


def _attention_factors(
    scores: dict[str, float],
) -> list[tuple[str, float]]:

    return sorted(
        [
            (factor, score)
            for factor, score in scores.items()
            if score < 60
        ],
        key=lambda item: item[1],
    )


def _metric_context(
    factor: str,
    metrics: dict,
) -> str:

    # -----------------------------------------------------
    # MARKET BEHAVIOUR
    # -----------------------------------------------------

    if factor == "market_behaviour":

        annualised_return = metrics.get(
            "annualised_return"
        )

        sharpe_ratio = metrics.get(
            "sharpe_ratio"
        )

        parts = []

        if annualised_return is not None:

            parts.append(
                f"annualised return of "
                f"{annualised_return:.2%}"
            )

        if sharpe_ratio is not None:

            parts.append(
                f"Sharpe ratio of "
                f"{sharpe_ratio:.2f}"
            )

        if parts:

            return (
                "This reflects the stock's recent "
                "historical market behaviour, including "
                + " and ".join(parts)
                + "."
            )

        return (
            "The score is based on the available "
            "historical market behaviour evidence."
        )


    # -----------------------------------------------------
    # RISK
    # -----------------------------------------------------

    if factor == "risk":

        volatility = metrics.get(
            "volatility"
        )

        max_drawdown = metrics.get(
            "max_drawdown"
        )

        parts = []

        if volatility is not None:

            parts.append(
                f"annualised volatility of "
                f"{volatility:.2%}"
            )

        if max_drawdown is not None:

            parts.append(
                f"maximum drawdown of "
                f"{max_drawdown:.2%}"
            )

        if parts:

            return (
                "This reflects the stock's historical "
                "risk characteristics, including "
                + " and ".join(parts)
                + "."
            )

        return (
            "The score is based on the available "
            "historical risk evidence."
        )


    # -----------------------------------------------------
    # FUNDAMENTALS
    # -----------------------------------------------------

    if factor == "fundamentals":

        fundamental_coverage = metrics.get(
            "fundamental_coverage"
        )

        parts = []

        pe_ratio = metrics.get(
            "pe_ratio"
        )

        profit_margin = metrics.get(
            "profit_margin"
        )

        debt_to_equity = metrics.get(
            "debt_to_equity"
        )

        if pe_ratio is not None:

            parts.append(
                f"P/E of {pe_ratio:.2f}"
            )

        if profit_margin is not None:

            parts.append(
                f"profit margin of "
                f"{profit_margin:.2%}"
            )

        if debt_to_equity is not None:

            parts.append(
                f"debt-to-equity of "
                f"{debt_to_equity:.2f}"
            )

        context = ""

        if parts:

            context = (
                " Key available metrics include "
                + ", ".join(parts)
                + "."
            )

        if fundamental_coverage is not None:

            context += (
                f" Fundamental data coverage is "
                f"{fundamental_coverage:.0f}%."
            )

        return (
            "The score reflects the available "
            "company fundamental evidence."
            + context
        )


    # -----------------------------------------------------
    # GROWTH
    # -----------------------------------------------------

    if factor == "growth":

        growth_coverage = metrics.get(
            "growth_coverage"
        )

        growth_components = metrics.get(
            "growth_components"
        )

        if growth_components:

            component_text = []

            for name, score in (
                growth_components.items()
            ):

                if score is not None:

                    component_text.append(
                        f"{name.replace('_', ' ').title()}: "
                        f"{score:.1f}/100"
                    )

            if component_text:

                result = (
                    "The growth score is based on "
                    "the available growth components: "
                    + ", ".join(component_text)
                    + "."
                )

            else:

                result = (
                    "The growth score is based on "
                    "the available growth evidence."
                )

        else:

            result = (
                "The growth score is based on "
                "the available growth evidence."
            )

        if growth_coverage is not None:

            result += (
                f" Growth data coverage is "
                f"{growth_coverage:.0f}%."
            )

        return result


    # -----------------------------------------------------
    # VALUATION
    # -----------------------------------------------------

    if factor == "valuation":

        pe_ratio = metrics.get(
            "pe_ratio"
        )

        forward_pe = metrics.get(
            "forward_pe"
        )

        valuation_coverage = metrics.get(
            "valuation_coverage"
        )

        parts = []

        if pe_ratio is not None:

            parts.append(
                f"trailing P/E of {pe_ratio:.2f}"
            )

        if forward_pe is not None:

            parts.append(
                f"Forward P/E of {forward_pe:.2f}"
            )

        if parts:

            result = (
                "The valuation score uses the available "
                "valuation indicators, including "
                + " and ".join(parts)
                + "."
            )

        else:

            result = (
                "The valuation score uses the "
                "available valuation indicators."
            )

        if valuation_coverage is not None:

            result += (
                f" Valuation evidence coverage is "
                f"{valuation_coverage:.0f}%."
            )

        return result


    # -----------------------------------------------------
    # PORTFOLIO FIT
    # -----------------------------------------------------

    if factor == "portfolio_fit":

        risk_tolerance = metrics.get(
            "risk_tolerance"
        )

        investor_horizon = metrics.get(
            "investor_horizon"
        )

        stock_horizon = metrics.get(
            "stock_horizon"
        )

        existing_exposure = metrics.get(
            "existing_exposure"
        )

        parts = []

        if risk_tolerance:

            parts.append(
                f"{risk_tolerance} risk tolerance"
            )

        if investor_horizon:

            parts.append(
                f"{investor_horizon} investor horizon"
            )

        if stock_horizon:

            parts.append(
                f"{stock_horizon} stock horizon"
            )

        if existing_exposure is not None:

            parts.append(
                f"{existing_exposure:.0f}% existing exposure"
            )

        if parts:

            return (
                "Portfolio Fit compares the investor "
                "profile with the stock characteristics, "
                "using "
                + ", ".join(parts)
                + "."
            )

        return (
            "Portfolio Fit reflects the available "
            "investor-profile and stock-horizon inputs."
        )


    return (
        "The score reflects the available evidence "
        "for this factor."
    )


def build_explanation(
    assessment: dict,
    metrics: dict | None = None,
) -> dict:

    if metrics is None:
        metrics = {}

    scores = assessment.get(
        "scores",
        {},
    )

    overall_score = assessment.get(
        "overall_score"
    )

    coverage = assessment.get(
        "coverage"
    )

    evidence_level = assessment.get(
        "evidence_level"
    )

    horizon = assessment.get(
        "horizon"
    )

    positive = _positive_factors(
        scores
    )

    attention = _attention_factors(
        scores
    )


    supporting_factors = []

    for factor, score in positive:

        supporting_factors.append(
            {
                "factor": _label(factor),
                "score": round(
                    score,
                    2,
                ),
                "description": (
                    f"{_label(factor)} has a "
                    f"{_describe_score(score)} "
                    f"score of {score:.1f}/100. "
                    f"{_metric_context(factor, metrics)}"
                ),
            }
        )


    attention_factors = []

    for factor, score in attention:

        attention_factors.append(
            {
                "factor": _label(factor),
                "score": round(
                    score,
                    2,
                ),
                "description": (
                    f"{_label(factor)} has a "
                    f"{_describe_score(score)} "
                    f"score of {score:.1f}/100. "
                    f"{_metric_context(factor, metrics)}"
                ),
            }
        )


    if overall_score is not None:

        summary = (
            f"For the {horizon} horizon, InvestIQ "
            f"calculates an evidence score of "
            f"{overall_score:.1f}/100 with "
            f"{coverage:.0f}% evidence coverage. "
            f"The available evidence is classified "
            f"as {str(evidence_level).lower()}."
        )

    else:

        summary = (
            "InvestIQ does not have enough scored "
            "evidence to calculate an overall assessment."
        )


    if positive and attention:

        interpretation = (
            "The evidence is mixed across the "
            "evaluated dimensions. Some factors "
            "provide stronger support, while other "
            "factors indicate areas that should be "
            "considered carefully."
        )

    elif positive:

        interpretation = (
            "Most available factors are in the "
            "stronger range within the current "
            "scoring framework."
        )

    elif attention:

        interpretation = (
            "Several available factors are below "
            "the stronger-score range and should "
            "be considered carefully alongside "
            "the remaining evidence."
        )

    else:

        interpretation = (
            "No factor-level interpretation "
            "is available."
        )


    return {
        "summary": summary,
        "interpretation": interpretation,
        "supporting_factors": supporting_factors,
        "attention_factors": attention_factors,
        "evidence_coverage": coverage,
        "evidence_level": evidence_level,
    }


def build_factor_explanation(
    factor: str,
    score: float,
    metrics: dict | None = None,
) -> str:

    if metrics is None:
        metrics = {}

    label = _label(factor)

    return (
        f"{label} is "
        f"{_describe_score(score)} "
        f"at {score:.1f}/100. "
        f"{_metric_context(factor, metrics)}"
    )