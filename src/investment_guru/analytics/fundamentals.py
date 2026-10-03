from __future__ import annotations

from typing import Any

import yfinance as yf


def _normalise_ticker(ticker: str) -> str:
    """
    Convert a user-entered Indian stock ticker into
    the Yahoo Finance format when necessary.
    """

    ticker = ticker.strip().upper()

    if ticker in {"NIFTY50", "NIFTY"}:
        return "^NSEI"

    if ticker.startswith("^"):
        return ticker

    if "." not in ticker:
        return f"{ticker}.NS"

    return ticker


def _safe_number(value: Any) -> float | None:
    """
    Convert a value into a float when possible.
    Return None when the value is unavailable or invalid.
    """

    if value is None:
        return None

    try:
        number = float(value)

        if number != number:
            return None

        return number

    except (TypeError, ValueError):
        return None


def get_fundamental_data(
    ticker: str,
) -> dict[str, Any]:
    """
    Retrieve fundamental company data from Yahoo Finance.

    Growth metrics are collected here as raw evidence,
    but they are not included in the Fundamental Score.
    They will be handled separately by the Growth factor.
    """

    yahoo_ticker = _normalise_ticker(ticker)

    stock = yf.Ticker(yahoo_ticker)

    try:
        info = stock.info
    except Exception:
        info = {}

    return {
        # -------------------------------------------------
        # COMPANY INFORMATION
        # -------------------------------------------------

        "Company": info.get("longName")
        or info.get("shortName"),

        "Sector": info.get("sector"),

        "Industry": info.get("industry"),

        # -------------------------------------------------
        # MARKET DATA
        # -------------------------------------------------

        "Market Cap": _safe_number(
            info.get("marketCap")
        ),

        # -------------------------------------------------
        # VALUATION
        # -------------------------------------------------

        "P/E Ratio": _safe_number(
            info.get("trailingPE")
        ),

        "Forward P/E": _safe_number(
            info.get("forwardPE")
        ),

        # -------------------------------------------------
        # EARNINGS
        # -------------------------------------------------

        "EPS": _safe_number(
            info.get("trailingEps")
        ),

        "Revenue": _safe_number(
            info.get("totalRevenue")
        ),

        # -------------------------------------------------
        # GROWTH
        # -------------------------------------------------
        # These are collected as raw metrics.
        # The Growth factor will score them separately.

        "Revenue Growth": _safe_number(
            info.get("revenueGrowth")
        ),

        "Earnings Growth": _safe_number(
            info.get("earningsGrowth")
        ),

        # -------------------------------------------------
        # PROFITABILITY
        # -------------------------------------------------

        "Profit Margin": _safe_number(
            info.get("profitMargins")
        ),

        "Return on Equity": _safe_number(
            info.get("returnOnEquity")
        ),

        # -------------------------------------------------
        # FINANCIAL RISK
        # -------------------------------------------------

        "Debt to Equity": _safe_number(
            info.get("debtToEquity")
        ),
    }


# =========================================================
# SCORING HELPERS
# =========================================================

def _score_higher_is_better(
    value: float | None,
    weak: float,
    strong: float,
) -> float | None:
    """
    Convert a metric where higher values are better
    into a 0-100 score.
    """

    if value is None:
        return None

    if value <= weak:
        return 0.0

    if value >= strong:
        return 100.0

    score = 100 * (
        (value - weak)
        / (strong - weak)
    )

    return round(
        max(0.0, min(100.0, score)),
        2,
    )


def _score_lower_is_better(
    value: float | None,
    good: float,
    expensive: float,
) -> float | None:
    """
    Convert a metric where lower values are better
    into a 0-100 score.
    """

    if value is None:
        return None

    if value <= good:
        return 100.0

    if value >= expensive:
        return 0.0

    score = 100 * (
        (expensive - value)
        / (expensive - good)
    )

    return round(
        max(0.0, min(100.0, score)),
        2,
    )


# =========================================================
# FUNDAMENTAL SCORING
# =========================================================

def calculate_fundamental_scores(
    fundamentals: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate the overall fundamental score.

    Fundamental framework:

    Profitability   -> 40%
    Valuation       -> 35%
    Financial Risk  -> 25%

    Growth metrics are intentionally excluded here.
    They are handled by the separate Growth factor.
    """

    # -----------------------------------------------------
    # PROFITABILITY
    # -----------------------------------------------------

    profit_margin = fundamentals.get(
        "Profit Margin"
    )

    return_on_equity = fundamentals.get(
        "Return on Equity"
    )

    profit_margin_score = _score_higher_is_better(
        profit_margin,
        weak=0.0,
        strong=0.20,
    )

    roe_score = _score_higher_is_better(
        return_on_equity,
        weak=0.0,
        strong=0.20,
    )

    profitability_scores = []

    if profit_margin_score is not None:
        profitability_scores.append(
            profit_margin_score
        )

    if roe_score is not None:
        profitability_scores.append(
            roe_score
        )

    if profitability_scores:
        profitability_score = (
            sum(profitability_scores)
            / len(profitability_scores)
        )
    else:
        profitability_score = None

    # -----------------------------------------------------
    # VALUATION
    # -----------------------------------------------------

    pe_ratio = fundamentals.get(
        "P/E Ratio"
    )

    forward_pe = fundamentals.get(
        "Forward P/E"
    )

    pe_score = _score_lower_is_better(
        pe_ratio,
        good=15.0,
        expensive=35.0,
    )

    forward_pe_score = _score_lower_is_better(
        forward_pe,
        good=12.0,
        expensive=30.0,
    )

    valuation_scores = []

    if pe_score is not None:
        valuation_scores.append(
            pe_score
        )

    if forward_pe_score is not None:
        valuation_scores.append(
            forward_pe_score
        )

    if valuation_scores:
        valuation_score = (
            sum(valuation_scores)
            / len(valuation_scores)
        )
    else:
        valuation_score = None

    # -----------------------------------------------------
    # FINANCIAL RISK
    # -----------------------------------------------------

    debt_to_equity = fundamentals.get(
        "Debt to Equity"
    )

    financial_risk_score = _score_lower_is_better(
        debt_to_equity,
        good=0.0,
        expensive=100.0,
    )

    # -----------------------------------------------------
    # OVERALL FUNDAMENTAL SCORE
    # -----------------------------------------------------

    component_scores = {
        "profitability": profitability_score,
        "valuation": valuation_score,
        "financial_risk": financial_risk_score,
    }

    weights = {
        "profitability": 0.40,
        "valuation": 0.35,
        "financial_risk": 0.25,
    }

    available_components = [
        component
        for component in weights
        if component_scores[component] is not None
    ]

    if available_components:

        available_weight = sum(
            weights[component]
            for component in available_components
        )

        weighted_score = sum(
            component_scores[component]
            * weights[component]
            for component in available_components
        )

        overall_score = (
            weighted_score
            / available_weight
        )

    else:
        overall_score = None

    # -----------------------------------------------------
    # COVERAGE
    # -----------------------------------------------------

    metric_keys = [
        "P/E Ratio",
        "Forward P/E",
        "Profit Margin",
        "Return on Equity",
        "Debt to Equity",
    ]

    available_metrics = sum(
        1
        for key in metric_keys
        if fundamentals.get(key) is not None
    )

    metric_coverage = (
        available_metrics
        / len(metric_keys)
        * 100
    )

    available_component_count = len(
        available_components
    )

    component_coverage = (
        available_component_count
        / len(weights)
        * 100
    )

    # -----------------------------------------------------
    # ASSESSMENT
    # -----------------------------------------------------

    if overall_score is None:

        assessment = (
            "Fundamental analysis unavailable"
        )

    elif overall_score >= 70:

        assessment = (
            "Strong fundamental profile"
        )

    elif overall_score >= 50:

        assessment = (
            "Moderate fundamental profile"
        )

    else:

        assessment = (
            "Weak fundamental profile"
        )

    # -----------------------------------------------------
    # RETURN RESULTS
    # -----------------------------------------------------

    return {
        "overall_score": (
            round(overall_score, 2)
            if overall_score is not None
            else None
        ),

        "coverage": round(
            metric_coverage,
            2,
        ),

        "component_coverage": round(
            component_coverage,
            2,
        ),

        "assessment": assessment,

        "components": {
            "profitability": (
                round(
                    profitability_score,
                    2,
                )
                if profitability_score is not None
                else None
            ),

            "valuation": (
                round(
                    valuation_score,
                    2,
                )
                if valuation_score is not None
                else None
            ),

            "financial_risk": (
                round(
                    financial_risk_score,
                    2,
                )
                if financial_risk_score is not None
                else None
            ),
        },

        "raw_metrics": {
            "profit_margin": profit_margin,
            "return_on_equity": return_on_equity,
            "pe_ratio": pe_ratio,
            "forward_pe": forward_pe,
            "debt_to_equity": debt_to_equity,
        },
    }