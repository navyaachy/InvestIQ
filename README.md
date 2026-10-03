
## Features

### Portfolio Analysis
- Quantity-based holdings
- Invested value and current value
- Profit/Loss
- Return percentage
- Portfolio allocation
- Sector exposure
- Concentration analysis

### Risk Analysis
- Annualized volatility
- Beta
- Maximum drawdown
- Portfolio concentration
- HHI
- Effective number of holdings
- Risk contribution
- Correlation analysis where available

### Stock Analysis
- Fundamentals
- Growth
- Valuation
- Market behaviour
- Historical risk
- Peer context
- Portfolio fit

### Explainable Assessment
InvestIQ combines market behaviour, risk, fundamentals, growth, valuation and portfolio fit.

The importance of these factors changes according to the selected investment horizon.

The system reports:
- Evidence score
- Evidence coverage
- Evidence level
- Factor-level scores
- Assessment
- Analytical horizon
- Confidence context

### What-If Analysis
Users can test deterministic price scenarios and see their effect on portfolio value.

These scenarios are calculations, not forecasts.

### Investment Goals
Users can define:
- Target amount
- Time horizon
- Monthly contribution

The system calculates progress and the remaining amount without assuming a future return.

### Historical Analysis
Historical portfolio behaviour can be analysed using:
- Portfolio return
- Volatility
- Maximum drawdown
- Benchmark return
- Individual holding performance

### News & Events
Recent company and business-event context is retrieved through Google News RSS.

### Monitoring & Alerts
Rule-based alerts can identify:
- Loss thresholds
- Gain thresholds
- High portfolio concentration

### Investment Analysis Report
A consolidated report includes:
- Executive snapshot
- Holdings
- Portfolio concentration
- Portfolio risk
- Stock-level evidence
- Historical context
- Alerts
- News context
- Research considerations
- Methodology and limitations

### Data Transparency
InvestIQ displays:
- Data source
- Retrieval timestamp
- Status
- Market-data freshness
- Historical-data source
- News-data source
- Methodology
- Limitations

## Decision Framework

InvestIQ uses different evidence weights depending on the investment horizon.

### Short-Term

| Factor | Weight |
|---|---:|
| Market Behaviour | 30% |
| Risk | 25% |
| Fundamentals | 10% |
| Growth | 10% |
| Valuation | 15% |
| Portfolio Fit | 10% |

### Medium-Term

| Factor | Weight |
|---|---:|
| Market Behaviour | 15% |
| Risk | 20% |
| Fundamentals | 20% |
| Growth | 15% |
| Valuation | 20% |
| Portfolio Fit | 10% |

### Long-Term

| Factor | Weight |
|---|---:|
| Market Behaviour | 5% |
| Risk | 15% |
| Fundamentals | 25% |
| Growth | 20% |
| Valuation | 25% |
| Portfolio Fit | 10% |

Scores are normalized using available evidence. Missing information is not silently converted into an assumed score.

### Portfolio Fit

Portfolio fit considers:
- Risk compatibility
- Existing portfolio exposure
- Investment-horizon compatibility

Portfolio fit is an analytical framework and does not automatically determine whether an investment is suitable.


## Data Sources

### Yahoo Finance via yfinance
Used for market prices, historical prices, fundamental information, valuation metrics and selected financial indicators.

### Google News RSS
Used for recent company news and business-event context.

Data availability depends on external providers.

## Technology Stack

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- yfinance
- Pydantic
- PyYAML
- pytest
- SQLite/cache components
- Git/GitHub

## Project Structure

`	ext
InvestIQ/
├── src/
│   └── investment_guru/
│       ├── domain/
│       ├── data/
│       ├── quality/
│       ├── analytics/
│       ├── decision/
│       └── ui/
├── tests/
├── data/
├── requirements.txt
└── README.md
`

## Running InvestIQ

From PowerShell, activate the virtual environment and run Streamlit from the project root.

    cd C:\InvestIQ\InvestIQ
    .\.venv\Scripts\Activate.ps1
    python -m streamlit run .\src\investment_guru\ui\app.py

## Running Tests

Run the automated test suite with pytest.

    python -m pytest -q

Python files can also be checked with compileall.

    python -m compileall -q .\src .\tests

## Design Principles

### Explainability
Major assessments should be traceable to identifiable evidence.

### Transparency
Data sources and retrieval timestamps are disclosed where available.

### No fabricated data
Unavailable metrics remain unavailable rather than being silently estimated.

### No guaranteed predictions
Historical analysis and what-if scenarios are not presented as guaranteed future outcomes.

### Reproducibility
Core analytics are implemented as independent Python modules and tested separately from the UI.

## Limitations

- Market data may be delayed or unavailable.
- Provider timestamps may differ from application session timestamps.
- Fundamental metrics vary in availability between companies.
- News feeds may contain broader market articles.
- Historical portfolio analysis is reconstructed from current holdings.
- What-if analysis is deterministic, not probabilistic.
- Portfolio fit is an analytical framework, not personalized financial advice.
- InvestIQ does not guarantee investment returns.
- InvestIQ does not automatically determine whether a user should buy or sell a security.

## Project Status

Core analytical functionality has been implemented, including portfolio analytics, portfolio risk, stock comparison, investment assessment, horizon analysis, what-if analysis, investment goals, historical analysis, news context, monitoring alerts, investment reporting, data transparency and automated testing.

Remaining development:
1. Final UI consolidation and polish
2. Deployment-ready packaging

## Disclaimer

InvestIQ is an educational and analytical decision-support project.

Information produced by the system should be independently evaluated before being used for financial decisions. Market data, financial metrics, historical performance and news information may contain inaccuracies or gaps.

InvestIQ does not guarantee future performance and does not constitute personalized financial advice.
