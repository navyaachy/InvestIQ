from __future__ import annotations

from datetime import date, timedelta

from src.investment_guru.data.providers.yfinance_provider import (
    YFinanceProvider,
)
from src.investment_guru.data.storage.sqlite_cache import SQLiteCache
from src.investment_guru.domain.models import (
    AnalysisRequest,
    AnalysisResult,
)
from src.investment_guru.quality.checks import check_price_quality


class AnalysisPipeline:
    """Orchestrates data collection, caching, and quality checks."""

    def __init__(
        self,
        provider: YFinanceProvider | None = None,
        cache: SQLiteCache | None = None,
    ) -> None:
        self.provider = provider or YFinanceProvider()
        self.cache = cache or SQLiteCache()

    def _get_price_data(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ):
        cached = self.cache.load(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
        )

        # Use cache only when it contains data from the
        # beginning of the requested period.
        cache_has_full_history = (
            not cached.empty
            and cached.index.min().date() <= start_date
        )

        if cache_has_full_history:
            from src.investment_guru.domain.models import PriceSeries

            return PriceSeries(
                ticker=ticker,
                start_date=cached.index.min().date(),
                end_date=cached.index.max().date(),
                data=cached,
            )

        # Requested period is longer than cached data.
        # Fetch the complete requested period from Yahoo Finance.
        price_series = self.provider.get_price_history(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
        )

        # Save newly downloaded data to the cache.
        self.cache.save(
            ticker=ticker,
            data=price_series.data,
        )

        return price_series

    def run(self, request: AnalysisRequest) -> AnalysisResult:
        """Run the Phase 1 analysis workflow."""

        end_date = request.end_date or date.today()

        start_date = request.start_date or (
            end_date - timedelta(days=365)
        )

        stock_data = self._get_price_data(
            ticker=request.ticker,
            start_date=start_date,
            end_date=end_date,
        )

        benchmark_data = self._get_price_data(
            ticker=request.benchmark,
            start_date=start_date,
            end_date=end_date,
        )

        # Convert the requested calendar-day period into an
        # approximate number of expected trading observations.
        #
        # Markets have approximately 252 trading sessions
        # per 365 calendar days. A 5% tolerance is applied
        # because the exact number varies with weekends,
        # exchange holidays, and the selected date range.
        expected_trading_days = max(
            20,
            round(
                request.min_history_days
                * 252
                / 365
                * 0.95
            ),
        )

        stock_quality = check_price_quality(
            stock_data,
            min_history_days=expected_trading_days,
        )

        benchmark_quality = check_price_quality(
            benchmark_data,
            min_history_days=expected_trading_days,
        )

        return AnalysisResult(
            ticker=request.ticker,
            benchmark=request.benchmark,
            stock_data=stock_data,
            benchmark_data=benchmark_data,
            stock_quality=stock_quality,
            benchmark_quality=benchmark_quality,
            metadata={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "phase": "Phase 1",
            },
        )