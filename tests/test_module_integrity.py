def test_core_modules_import():
    from src.investment_guru.analytics import portfolio
    from src.investment_guru.analytics import portfolio_risk
    from src.investment_guru.analytics import growth
    from src.investment_guru.analytics import horizon
    from src.investment_guru.analytics import portfolio_fit
    from src.investment_guru.analytics import valuation
    from src.investment_guru.analytics import fundamentals
    from src.investment_guru.analytics import extended_fundamentals
    from src.investment_guru.analytics import valuation_context
    from src.investment_guru.analytics import peer_context


def test_decision_modules_import():
    from src.investment_guru.decision import assessment
    from src.investment_guru.decision import explain
    from src.investment_guru.decision import considerations


def test_data_modules_import():
    from src.investment_guru.data import data_freshness
    from src.investment_guru.data.providers import yfinance_provider
    from src.investment_guru.data.providers import portfolio_prices


def test_quality_and_pipeline_import():
    from src.investment_guru.quality import checks
    from src.investment_guru import pipeline
