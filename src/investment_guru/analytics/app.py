from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from src.investment_guru.domain.models import AnalysisRequest
from src.investment_guru.pipeline import AnalysisPipeline

from src.investment_guru.analytics.performance import (
    calculate_annualised_return,
    calculate_daily_returns,
    calculate_total_return,
)

from src.investment_guru.analytics.risk import (
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_volatility,
)

from src.investment_guru.analytics.fundamentals import (
    get_fundamental_data,
    calculate_fundamental_scores,
)

from src.investment_guru.analytics.valuation import (
    calculate_valuation_scores,
)

from src.investment_guru.analytics.growth import (
    calculate_growth_scores,
)

from src.investment_guru.analytics.peer_context import (
    build_peer_context,
)

from src.investment_guru.analytics.extended_fundamentals import (
    enrich_fundamental_data,
)

from src.investment_guru.analytics.horizon import (
    classify_stock_horizon,
)

from src.investment_guru.analytics.portfolio_fit import (
    calculate_portfolio_fit,
)

from src.investment_guru.decision.assessment import (
    build_assessment,
)

from src.investment_guru.decision.explain import (
    build_explanation,
)

from src.investment_guru.decision.considerations import (
    build_decision_considerations,
)
from src.investment_guru.decision.evidence_profile import (
    build_evidence_profile,
)


# =========================================================
# HELPERS
# =========================================================

def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def return_score(value: float) -> float:
    return round(
        clamp(50 + value * 200),
        2,
    )


def sharpe_score(value: float) -> float:
    return round(
        clamp(50 + value * 25),
        2,
    )


def volatility_score(value: float) -> float:
    return round(
        clamp(100 - value * 300),
        2,
    )


def drawdown_score(value: float) -> float:
    return round(
        clamp(100 + value * 150),
        2,
    )


def market_risk_scores(
    annualised_return: float,
    sharpe_ratio: float,
    volatility: float,
    max_drawdown: float,
) -> dict[str, float]:

    return {
        "market_behaviour": round(
            return_score(annualised_return) * 0.60
            + sharpe_score(sharpe_ratio) * 0.40,
            2,
        ),
        "risk": round(
            volatility_score(volatility) * 0.50
            + drawdown_score(max_drawdown) * 0.50,
            2,
        ),
    }


def label(name: str) -> str:
    return name.replace(
        "_",
        " ",
    ).title()


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="InvestIQ",
    page_icon="📊",
    layout="wide",
)


# =========================================================
# HEADER
# =========================================================

st.title(
    "InvestIQ"
)

st.caption(
    "An Explainable Investment Decision-Support System"
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header(
    "Analysis Settings"
)

ticker = st.sidebar.text_input(
    "Stock ticker",
    "RELIANCE",
)

benchmark = st.sidebar.text_input(
    "Benchmark",
    "^NSEI",
)

horizon = st.sidebar.selectbox(
    "Investment Horizon",
    [
        "short-term",
        "medium-term",
        "long-term",
    ],
    index=2,
)

days = st.sidebar.slider(
    "History (days)",
    30,
    1825,
    365,
)

st.sidebar.caption(
    "The selected horizon changes the relative "
    "importance of decision factors."
)

st.sidebar.divider()

st.sidebar.header(
    "Investor Profile"
)

risk_tolerance = st.sidebar.selectbox(
    "Risk tolerance",
    [
        "conservative",
        "moderate",
        "aggressive",
    ],
    index=1,
)

investment_amount = st.sidebar.number_input(
    "Investment amount (₹)",
    min_value=0,
    value=50000,
    step=5000,
)

existing_exposure = st.sidebar.slider(
    "Existing stock exposure (%)",
    0,
    100,
    0,
)

st.sidebar.caption(
    "Investment amount is contextual. It is not scored "
    "because InvestIQ does not know your total "
    "investable capital."
)

run_analysis = st.sidebar.button(
    "Run Analysis",
    type="primary",
)


# =========================================================
# INITIAL STATE
# =========================================================

if not run_analysis:

    st.info(
        "Enter a stock ticker and click "
        "'Run Analysis' to begin."
    )

    st.stop()


# =========================================================
# DATA PIPELINE
# =========================================================

with st.spinner(
    "Collecting and validating market data..."
):

    request = AnalysisRequest(
        ticker=ticker.strip().upper(),
        benchmark=benchmark.strip().upper(),
        start_date=date.today() - timedelta(days=days),
        end_date=date.today(),
    )

    result = AnalysisPipeline().run(
        request
    )


st.subheader(
    f"{result.ticker} Analysis"
)


# =========================================================
# DATA QUALITY
# =========================================================

st.markdown(
    "### Data Quality"
)

c1, c2 = st.columns(2)

with c1:

    st.metric(
        "Stock Data Rows",
        (
            result.stock_data.row_count
            if result.stock_data
            else 0
        ),
    )

    st.write(
        "Stock quality:",
        (
            result.stock_quality.status.value
            if result.stock_quality
            else "Unavailable"
        ),
    )


with c2:

    st.metric(
        "Benchmark Data Rows",
        (
            result.benchmark_data.row_count
            if result.benchmark_data
            else 0
        ),
    )

    st.write(
        "Benchmark quality:",
        (
            result.benchmark_quality.status.value
            if result.benchmark_quality
            else "Unavailable"
        ),
    )


# =========================================================
# PERFORMANCE + RISK
# =========================================================

total_return = None
annualised_return = None
daily_returns = None

volatility = None
max_drawdown = None
sharpe_ratio = None


if result.stock_data:

    data = result.stock_data.data

    total_return = calculate_total_return(
        data
    )

    annualised_return = calculate_annualised_return(
        data
    )

    daily_returns = calculate_daily_returns(
        data
    )

    st.subheader(
        "Performance Analysis"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Return",
        f"{total_return:.2%}",
    )

    c2.metric(
        "Annualised Return",
        f"{annualised_return:.2%}",
    )

    c3.metric(
        "Trading Days",
        len(daily_returns),
    )

    volatility = calculate_volatility(
        data
    )

    max_drawdown = calculate_max_drawdown(
        data
    )

    sharpe_ratio = calculate_sharpe_ratio(
        data
    )

    st.subheader(
        "Risk Analysis"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Annualised Volatility",
        f"{volatility:.2%}",
    )

    c2.metric(
        "Maximum Drawdown",
        f"{max_drawdown:.2%}",
    )

    c3.metric(
        "Sharpe Ratio",
        f"{sharpe_ratio:.2f}",
    )


# =========================================================
# FUNDAMENTAL / VALUATION / GROWTH DATA
# =========================================================

with st.spinner(
    "Loading fundamental data..."
):

    fundamentals = get_fundamental_data(
        result.ticker
    )

    fundamentals = enrich_fundamental_data(
        ticker=result.ticker,
        fundamentals=fundamentals,
    )

    fundamental_scores = (
        calculate_fundamental_scores(
            fundamentals
        )
    )

    valuation_scores = (
        calculate_valuation_scores(
            fundamentals
        )
    )

    growth_scores = (
        calculate_growth_scores(
            fundamentals
        )
    )

    peer_context = build_peer_context(
        ticker=result.ticker,
        fundamentals=fundamentals,
    )


# =========================================================
# DECISION ENGINE
# =========================================================

if all(
    value is not None
    for value in (
        annualised_return,
        sharpe_ratio,
        volatility,
        max_drawdown,
    )
):

    # =====================================================
    # MARKET + RISK
    # =====================================================

    scores = market_risk_scores(
        annualised_return=annualised_return,
        sharpe_ratio=sharpe_ratio,
        volatility=volatility,
        max_drawdown=max_drawdown,
    )


    # =====================================================
    # FUNDAMENTALS
    # =====================================================

    fundamental_score = (
        fundamental_scores.get(
            "overall_score"
        )
    )

    if fundamental_score is not None:

        scores[
            "fundamentals"
        ] = fundamental_score


    # =====================================================
    # VALUATION
    # =====================================================

    valuation_score = (
        valuation_scores.get(
            "overall_score"
        )
    )

    if valuation_score is not None:

        scores[
            "valuation"
        ] = valuation_score


    # =====================================================
    # GROWTH
    # =====================================================

    growth_score = (
        growth_scores.get(
            "overall_score"
        )
    )

    if growth_score is not None:

        scores[
            "growth"
        ] = growth_score


    # =====================================================
    # ANALYTICAL STOCK HORIZON
    # =====================================================

    stock_horizon_result = (
        classify_stock_horizon(
            market_behaviour=scores.get(
                "market_behaviour"
            ),
            fundamentals=scores.get(
                "fundamentals"
            ),
            growth=scores.get(
                "growth"
            ),
            valuation=scores.get(
                "valuation"
            ),
        )
    )

    stock_horizon = (
        stock_horizon_result.get(
            "horizon"
        )
    )


    # =====================================================
    # PORTFOLIO FIT
    # =====================================================

    portfolio_fit = None

    if stock_horizon is not None:

        portfolio_fit = (
            calculate_portfolio_fit(
                risk_score=scores.get(
                    "risk"
                ),
                risk_tolerance=risk_tolerance,
                investor_horizon=horizon,
                stock_horizon=stock_horizon,
                investment_amount=(
                    investment_amount
                    if investment_amount > 0
                    else None
                ),
                existing_exposure=existing_exposure,
            )
        )

        portfolio_score = (
            portfolio_fit.get(
                "overall_score"
            )
        )

        if portfolio_score is not None:

            scores[
                "portfolio_fit"
            ] = portfolio_score


    # =====================================================
    # OVERALL ASSESSMENT
    # =====================================================

    assessment = build_assessment(
        scores=scores,
        horizon=horizon,
    )


    # =====================================================
    # EXPLANATION
    # =====================================================

    explanation = build_explanation(
        assessment
    )


    # =====================================================
    # DECISION CONSIDERATIONS
    # =====================================================

    decision_considerations = (
        build_decision_considerations(
            scores
        )
    )


    # =====================================================
    # EVIDENCE PROFILE
    # =====================================================

    evidence_profile = build_evidence_profile(
        scores={
            "market_behaviour": scores.get(
                "market_behaviour"
            ),
            "risk": scores.get(
                "risk"
            ),
            "fundamentals": scores.get(
                "fundamentals"
            ),
            "growth": scores.get(
                "growth"
            ),
            "valuation": scores.get(
                "valuation"
            ),
        }
    )


    # =====================================================
    # EVIDENCE PROFILE
    # =====================================================

    st.subheader(
        "Evidence Profile"
    )

    st.caption(
        "InvestIQ keeps each analytical dimension separate so "
        "you can see what the evidence supports, where it is "
        "mixed, and where further investigation is needed."
    )

    st.info(
        f"Analysis Lens: **{horizon.title()}**  |  "
        "This lens changes which evidence receives more analytical "
        "emphasis. It does not classify the stock as short-term, "
        "medium-term, or long-term."
    )

    profile_columns = st.columns(5)

    for column, dimension in zip(
        profile_columns,
        evidence_profile["dimensions"],
    ):

        with column:

            with st.container(border=True):

                st.caption(
                    dimension["label"]
                )

                st.markdown(
                    f"### {dimension['rating']}"
                )

                if dimension["available"]:
                    st.caption(
                        dimension["reason"]
                    )
                else:
                    st.caption(
                        "Evidence unavailable."
                    )

    st.caption(
        f"Evidence available across "
        f"**{evidence_profile['available_dimensions']} "
        f"of {evidence_profile['total_dimensions']} "
        f"dimensions** "
        f"({evidence_profile['completeness']:.0f}% completeness)."
    )


    # =====================================================
    # WHAT THE EVIDENCE SHOWS
    # =====================================================

    st.markdown(
        "### What the Evidence Shows"
    )

    supporting = [
        item["label"]
        for item in evidence_profile["dimensions"]
        if item["rating"] in {"Strong", "Supportive"}
    ]

    mixed = [
        item["label"]
        for item in evidence_profile["dimensions"]
        if item["rating"] == "Mixed"
    ]

    attention = [
        item["label"]
        for item in evidence_profile["dimensions"]
        if item["rating"] in {"Weak", "Not enough data"}
    ]

    if supporting:
        st.success(
            "**Stronger evidence:** "
            + ", ".join(supporting)
            + "."
        )

    if mixed:
        st.info(
            "**Mixed evidence:** "
            + ", ".join(mixed)
            + "."
        )

    if attention:
        st.warning(
            "**Needs attention:** "
            + ", ".join(attention)
            + "."
        )

    st.caption(
        "These are descriptive evidence labels. They are not "
        "buy, sell, hold, or price-prediction signals."
    )


    # =====================================================
    # SUPPORTING EVIDENCE
    # =====================================================

    st.markdown(
        "#### Supporting Evidence"
    )

    if explanation[
        "supporting_factors"
    ]:

        for factor in explanation[
            "supporting_factors"
        ]:

            st.write(
                f"**{factor['factor']}** "
                f"• {factor['score']:.1f}/100"
            )

            st.caption(
                factor[
                    "description"
                ]
            )

    else:

        st.write(
            "No factors are currently in the "
            "stronger-score range."
        )


    # =====================================================
    # FACTORS REQUIRING ATTENTION
    # =====================================================

    st.markdown(
        "#### Factors Requiring Attention"
    )

    if explanation[
        "attention_factors"
    ]:

        for factor in explanation[
            "attention_factors"
        ]:

            st.write(
                f"**{factor['factor']}** "
                f"• {factor['score']:.1f}/100"
            )

            st.caption(
                factor[
                    "description"
                ]
            )

    else:

        st.write(
            "No available factors are currently "
            "below the stronger-score range."
        )


    # =====================================================
    # DECISION CONSIDERATIONS
    # =====================================================

    st.markdown(
        "### Decision Considerations"
    )

    st.caption(
        "These are evidence-based areas to investigate "
        "further. They are not buy, sell, or hold "
        "recommendations."
    )


    # -----------------------------------------------------
    # KEY CONSIDERATIONS
    # -----------------------------------------------------

    st.markdown(
        "#### Key Considerations"
    )

    considerations = (
        decision_considerations[
            "key_considerations"
        ]
    )

    if considerations:

        for item in considerations:

            st.write(
                f"**{item['factor']}** "
                f"• {item['score']:.1f}/100"
            )

            st.write(
                item["text"]
            )

    else:

        st.write(
            "No decision considerations are available "
            "from the current evidence."
        )
    st.caption(
        "InvestIQ surfaces evidence for further investigation "
        "rather than automatically converting the evidence "
        "into a trading recommendation."
    )


    # =====================================================
    # EVIDENCE PROFILE DETAIL
    # =====================================================

    st.markdown(
        "### Evidence Profile Detail"
    )

    st.caption(
        "Each dimension is shown independently so that "
        "strengths and weaknesses are not collapsed into "
        "one composite number."
    )

    profile_rows = []

    for dimension in evidence_profile["dimensions"]:

        profile_rows.append(
            {
                "Dimension": dimension["label"],
                "Rating": dimension["rating"],
                "Evidence": (
                    "Available"
                    if dimension["available"]
                    else "Unavailable"
                ),
                "Interpretation": dimension["reason"],
            }
        )

    st.table(
        profile_rows
    )

    st.caption(
        "The ratings summarize the underlying analytical "
        "scores for readability. They are descriptive evidence "
        "labels, not investment recommendations."
    )


    # =====================================================
    # ANALYTICAL STOCK HORIZON
    # =====================================================

    st.markdown(
        "### Analytical Stock Horizon"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Stock Horizon",
        (
            stock_horizon.title()
            if stock_horizon
            else "N/A"
        ),
    )

    c2.metric(
        "Classification Confidence",
        stock_horizon_result.get(
            "confidence",
            "N/A",
        ),
    )

    c3.metric(
        "Evidence Components",
        (
            f"{stock_horizon_result.get('components_available', 0)}/4"
        ),
    )

    st.write(
        "**Why this horizon?**"
    )

    st.write(
        stock_horizon_result.get(
            "reason",
            "Unavailable.",
        )
    )

    c1, c2 = st.columns(2)

    short_term = (
        stock_horizon_result.get(
            "short_term_score"
        )
    )

    long_term = (
        stock_horizon_result.get(
            "long_term_score"
        )
    )

    c1.metric(
        "Short-Term Evidence",
        (
            f"{short_term:.1f}/100"
            if short_term is not None
            else "N/A"
        ),
    )

    c2.metric(
        "Long-Term Evidence",
        (
            f"{long_term:.1f}/100"
            if long_term is not None
            else "N/A"
        ),
    )


    # =====================================================
    # PORTFOLIO FIT
    # =====================================================

    st.markdown(
        "### Portfolio Fit"
    )

    if portfolio_fit is not None:

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Portfolio Fit Score",
            (
                f"{portfolio_fit['overall_score']:.1f}/100"
            ),
        )

        c2.metric(
            "Portfolio Fit Coverage",
            (
                f"{portfolio_fit['coverage']:.0f}%"
            ),
        )

        with c3:

            st.write(
                "**Assessment**"
            )

            st.write(
                portfolio_fit[
                    "assessment"
                ]
            )

        with c4:

            st.write(
                "**Risk Tolerance**"
            )

            st.write(
                risk_tolerance.title()
            )


        component_labels = {
            "risk_fit":
                "Risk Compatibility",

            "exposure_fit":
                "Existing Exposure",

            "horizon_fit":
                "Horizon Compatibility",
        }


        portfolio_rows = []

        for component, score in (
            portfolio_fit[
                "components"
            ].items()
        ):

            portfolio_rows.append(
                {
                    "Component":
                        component_labels.get(
                            component,
                            label(component),
                        ),

                    "Score":
                        (
                            f"{score:.1f}/100"
                            if score is not None
                            else "N/A"
                        ),

                    "Weight":
                        (
                            f"{portfolio_fit['weights'][component]:.0%}"
                        ),
                }
            )

        st.table(
            portfolio_rows
        )

        st.caption(
            "Portfolio Fit compares stated risk tolerance, "
            "intended horizon, and existing stock exposure "
            "with the available evidence. It is not a "
            "financial suitability determination."
        )

    else:

        st.warning(
            "Portfolio Fit could not be calculated because "
            "the stock horizon could not be classified."
        )


    # =====================================================
    # AVAILABLE FACTOR CONTRIBUTION
    # =====================================================

    st.markdown(
        "### Available Factor Contribution"
    )

    contribution_rows = []

    for factor in assessment[
        "factors"
    ]:

        contribution_rows.append(
            {
                "Factor":
                    label(
                        factor["factor"]
                    ),

                "Score":
                    (
                        f"{factor['score']:.1f}/100"
                    ),

                "Weight":
                    (
                        f"{factor['weight']:.0%}"
                    ),

                "Contribution":
                    (
                        f"{factor['contribution']:.1f}"
                    ),
            }
        )

    st.table(
        contribution_rows
    )


    # =====================================================
    # HORIZON-BASED WEIGHTING
    # =====================================================

    st.markdown(
        "### Horizon-Based Weighting"
    )

    st.write(
        "The framework changes the relative importance "
        "of each factor according to the selected "
        "investment horizon."
    )

    weight_rows = []

    for factor, weight in (
        assessment[
            "weights"
        ].items()
    ):

        weight_rows.append(
            {
                "Factor":
                    label(factor),

                "Weight":
                    f"{weight:.0%}",

                "Status":
                    (
                        "Available"
                        if factor in scores
                        else "Not yet available"
                    ),
            }
        )

    st.table(
        weight_rows
    )


    # =====================================================
    # MISSING FACTORS
    # =====================================================

    missing_factors = [
        factor
        for factor in assessment[
            "weights"
        ]
        if factor not in scores
    ]

    if missing_factors:

        st.warning(
            "Some analytical dimensions are not currently "
            "available: "
            + ", ".join(
                label(factor)
                for factor in missing_factors
            )
            + "."
        )


    # =====================================================
    # FUNDAMENTAL + VALUATION EVIDENCE
    # =====================================================

    st.markdown(
        "### Fundamental & Valuation Evidence"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Fundamental Score",
        (
            f"{fundamental_score:.1f}/100"
            if fundamental_score is not None
            else "N/A"
        ),
    )

    c2.metric(
        "Fundamental Coverage",
        (
            f"{fundamental_scores['coverage']:.0f}%"
        ),
    )

    c3.metric(
        "Valuation Score",
        (
            f"{valuation_score:.1f}/100"
            if valuation_score is not None
            else "N/A"
        ),
    )

    c4.metric(
        "Valuation Coverage",
        (
            f"{valuation_scores['coverage']:.0f}%"
        ),
    )

    st.caption(
        "Fundamental component coverage: "
        f"{fundamental_scores['component_coverage']:.0f}%"
    )


    # =====================================================
    # GROWTH EVIDENCE
    # =====================================================

    st.markdown(
        "### Growth Evidence"
    )

    c1, c2 = st.columns(2)

    c1.metric(
        "Growth Score",
        (
            f"{growth_score:.1f}/100"
            if growth_score is not None
            else "N/A"
        ),
    )

    c2.metric(
        "Growth Coverage",
        (
            f"{growth_scores['coverage']:.0f}%"
        ),
    )

    st.write(
        f"**Growth Assessment:** "
        f"{growth_scores['assessment']}"
    )

    growth_rows = []

    for name, score in (
        growth_scores[
            "components"
        ].items()
    ):

        growth_rows.append(
            {
                "Metric":
                    label(name),

                "Score":
                    (
                        f"{score:.1f}/100"
                        if score is not None
                        else "N/A"
                    ),
            }
        )

    st.table(
        growth_rows
    )

    st.caption(
        "Growth scoring uses current Revenue Growth "
        "and Earnings Growth data. These metrics are "
        "separate from the Fundamental Score."
    )


    # =====================================================
    # VALUATION EVIDENCE
    # =====================================================

    st.markdown(
        "### Valuation Evidence"
    )

    st.write(
        f"**Valuation Assessment:** "
        f"{valuation_scores['assessment']}"
    )

    valuation_rows = []

    for name, score in (
        valuation_scores[
            "components"
        ].items()
    ):

        valuation_rows.append(
            {
                "Metric":
                    label(name),

                "Score":
                    (
                        f"{score:.1f}/100"
                        if score is not None
                        else "N/A"
                    ),
            }
        )

    st.table(
        valuation_rows
    )

    st.caption(
        "Valuation scoring currently uses transparent "
        "P/E and Forward P/E heuristics. It is not a "
        "fair-value estimate."
    )


# =========================================================
# SECTOR / PEER-RELATIVE CONTEXT
# =========================================================

st.subheader(
    "Sector & Peer Context"
)

if peer_context["available"]:

    st.caption(
        f"Sector: **{peer_context.get('sector') or 'Unavailable'}**  |  "
        f"Industry: **{peer_context.get('industry') or 'Unavailable'}**  |  "
        f"Reference set: **{len(peer_context['peer_tickers'])} stocks**"
    )

    peer_rows = []

    display_metrics = [
        ("P/E Ratio", "P/E"),
        ("Forward P/E", "Forward P/E"),
        ("Return on Equity", "ROE"),
        ("Debt to Equity", "Debt / Equity"),
        ("Profit Margin", "Profit Margin"),
        ("Revenue Growth", "Revenue Growth"),
    ]

    for metric_name, display_name in display_metrics:
        metric = peer_context["metrics"].get(metric_name, {})
        target = metric.get("target")
        peer_median = metric.get("peer_median")

        if target is None and peer_median is None:
            target_text = "N/A"
            median_text = "N/A"
        elif metric_name in {"Return on Equity", "Profit Margin", "Revenue Growth"}:
            target_text = f"{target:.2%}" if target is not None else "N/A"
            median_text = f"{peer_median:.2%}" if peer_median is not None else "N/A"
        else:
            target_text = f"{target:.2f}" if target is not None else "N/A"
            median_text = f"{peer_median:.2f}" if peer_median is not None else "N/A"

        peer_rows.append(
            {
                "Metric": display_name,
                "Stock": target_text,
                "Peer median": median_text,
                "Relative context": metric.get("relative", "Not available"),
                "Peers used": metric.get("peer_count", 0),
            }
        )

    st.dataframe(
        peer_rows,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Reference peers: "
        + ", ".join(peer_context["peer_tickers"])
    )

    st.info(
        "Peer-relative values provide context, not a verdict. "
        "The reference set is curated and is not the full sector universe."
    )

else:

    st.info(
        peer_context["message"]
    )


# =========================================================
# FUNDAMENTAL ANALYSIS
# =========================================================

st.subheader(
    "Fundamental Analysis"
)

for key, title in [
    (
        "Company",
        "Company",
    ),
    (
        "Sector",
        "Sector",
    ),
    (
        "Industry",
        "Industry",
    ),
]:

    value = fundamentals.get(
        key
    )

    if value:

        st.write(
            f"**{title}:** {value}"
        )


metric_specs = [
    (
        "Market Cap",
        "Market Cap",
        lambda x: f"₹{x / 1e12:.2f}T",
    ),
    (
        "P/E Ratio",
        "P/E Ratio",
        lambda x: f"{x:.2f}",
    ),
    (
        "Forward P/E",
        "Forward P/E",
        lambda x: f"{x:.2f}",
    ),
    (
        "EPS",
        "EPS",
        lambda x: f"₹{x:.2f}",
    ),
    (
        "Revenue",
        "Revenue",
        lambda x: f"₹{x / 1e12:.2f}T",
    ),
    (
        "Profit Margin",
        "Profit Margin",
        lambda x: f"{x:.2%}",
    ),
    (
        "Revenue Growth",
        "Revenue Growth",
        lambda x: f"{x:.2%}",
    ),
    (
        "Earnings Growth",
        "Earnings Growth",
        lambda x: f"{x:.2%}",
    ),
    (
        "Return on Equity",
        "Return on Equity",
        lambda x: f"{x:.2%}",
    ),
    (
        "Debt to Equity",
        "Debt to Equity",
        lambda x: f"{x:.2f}",
    ),
]


for start in range(
    0,
    len(metric_specs),
    3,
):

    cols = st.columns(3)

    for col, (
        key,
        title,
        formatter,
    ) in zip(
        cols,
        metric_specs[
            start:start + 3
        ],
    ):

        value = fundamentals.get(
            key
        )

        col.metric(
            title,
            (
                formatter(value)
                if value is not None
                else "N/A"
            ),
        )


# =========================================================
# EXTENDED FUNDAMENTAL ANALYSIS
# =========================================================

st.markdown(
    "### Extended Fundamental Analysis"
)

st.caption(
    "Additional profitability, balance-sheet, cash-flow and shareholder-return "
    "metrics. Values are shown only when the data provider supplies enough "
    "information to calculate them."
)

extended_metric_specs = [
    ("Return on Equity", "ROE", lambda x: f"{x:.2%}"),
    ("ROCE", "ROCE", lambda x: f"{x:.2%}"),
    ("Debt to Equity", "Debt / Equity", lambda x: f"{x:.2f}"),
    ("Interest Coverage", "Interest Coverage", lambda x: f"{x:.2f}x"),
    ("Operating Margin", "Operating Margin", lambda x: f"{x:.2%}"),
    ("Profit Margin", "Net Profit Margin", lambda x: f"{x:.2%}"),
    ("Free Cash Flow", "Free Cash Flow", lambda x: f"₹{x / 1e9:.2f}B"),
    ("Operating Cash Flow", "Operating Cash Flow", lambda x: f"₹{x / 1e9:.2f}B"),
    ("FCF Conversion", "FCF / Operating Cash Flow", lambda x: f"{x:.2%}"),
    ("Dividend Yield", "Dividend Yield", lambda x: f"{x:.2%}"),
    ("Payout Ratio", "Payout Ratio", lambda x: f"{x:.2%}"),
    ("Price to Book", "P/B", lambda x: f"{x:.2f}x"),
    ("EV / EBITDA", "EV / EBITDA", lambda x: f"{x:.2f}x"),
    ("Enterprise Value", "Enterprise Value", lambda x: f"₹{x / 1e12:.2f}T"),
]

for start in range(0, len(extended_metric_specs), 4):
    cols = st.columns(4)

    for col, (key, title, formatter) in zip(
        cols,
        extended_metric_specs[start:start + 4],
    ):
        value = fundamentals.get(key)

        col.metric(
            title,
            formatter(value) if value is not None else "N/A",
        )

st.caption(
    "ROCE is calculated as EBIT divided by capital employed when the required "
    "statement values are available. FCF conversion is Free Cash Flow divided "
    "by Operating Cash Flow. These metrics are descriptive and are not used as "
    "standalone buy/sell signals."
)


# =========================================================
# FUNDAMENTAL SCORE BREAKDOWN
# =========================================================

st.markdown(
    "### Fundamental Score Breakdown"
)

st.table(
    [
        {
            "Component":
                label(name),

            "Score":
                (
                    f"{score:.1f}/100"
                    if score is not None
                    else "N/A"
                ),
        }

        for name, score
        in fundamental_scores[
            "components"
        ].items()
    ]
)


# =========================================================
# VALUATION SCORE BREAKDOWN
# =========================================================

st.markdown(
    "### Valuation Score Breakdown"
)

st.table(
    [
        {
            "Component":
                label(name),

            "Score":
                (
                    f"{score:.1f}/100"
                    if score is not None
                    else "N/A"
                ),
        }

        for name, score
        in valuation_scores[
            "components"
        ].items()
    ]
)


# =========================================================
# PRICE CHART
# =========================================================

if result.stock_data:

    st.subheader(
        "Stock Price History"
    )

    st.line_chart(
        result.stock_data.data[
            "Close"
        ]
    )


# =========================================================
# BENCHMARK CHART
# =========================================================

if result.benchmark_data:

    st.subheader(
        "Benchmark Price History"
    )

    st.line_chart(
        result.benchmark_data.data[
            "Close"
        ]
    )


# =========================================================
# DATA QUALITY WARNINGS
# =========================================================

if (
    result.stock_quality
    and result.stock_quality.issues
):

    st.warning(
        "Stock data quality issues detected."
    )

    for issue in (
        result.stock_quality.issues
    ):

        st.write(
            f"- {issue}"
        )
