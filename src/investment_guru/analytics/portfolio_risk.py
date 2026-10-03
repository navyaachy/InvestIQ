from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf


def _ticker(value: Any) -> str:
    return str(value or "").strip().upper()


def _float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        value = float(value)
        return value if np.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def _normalise_holdings(holdings: list[dict[str, Any]]) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for row in holdings or []:
        ticker = _ticker(row.get("Ticker"))
        qty = _float(row.get("Quantity", row.get("Qty")))
        current = _float(row.get("Current Price", row.get("current_price")))
        if ticker and qty and qty > 0 and current and current > 0:
            rows.append({"Ticker": ticker, "Quantity": qty, "Current Price": current})
    return rows


def _download_prices(tickers: list[str], period: str = "1y") -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame()
    try:
        raw = yf.download(
            tickers=tickers,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception:
        return pd.DataFrame()

    if raw is None or raw.empty:
        return pd.DataFrame()

    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            prices = raw["Close"].copy()
        elif "Adj Close" in raw.columns.get_level_values(0):
            prices = raw["Adj Close"].copy()
        else:
            return pd.DataFrame()
    else:
        close_name = "Close" if "Close" in raw.columns else "Adj Close"
        if close_name not in raw.columns:
            return pd.DataFrame()
        prices = raw[[close_name]].copy()
        prices.columns = [tickers[0]]

    prices = prices.apply(pd.to_numeric, errors="coerce").dropna(how="all")
    prices = prices[[c for c in prices.columns if c in tickers]]
    return prices.dropna(axis=1, how="all")


def _annualised_volatility(returns: pd.Series) -> float | None:
    if returns.dropna().shape[0] < 20:
        return None
    return float(returns.std() * np.sqrt(252))


def _max_drawdown(prices: pd.Series) -> float | None:
    clean = prices.dropna()
    if clean.empty:
        return None
    drawdown = clean / clean.cummax() - 1.0
    return float(drawdown.min())


def _beta(stock_returns: pd.Series, benchmark_returns: pd.Series) -> float | None:
    joined = pd.concat([stock_returns, benchmark_returns], axis=1).dropna()
    if len(joined) < 30:
        return None
    market_var = float(joined.iloc[:, 1].var())
    if market_var == 0:
        return None
    return float(joined.iloc[:, 0].cov(joined.iloc[:, 1]) / market_var)


def _risk_level(largest_weight: float, hhi: float, effective_n: float) -> str:
    if largest_weight >= 0.50 or hhi >= 0.40 or effective_n < 2.0:
        return "High concentration"
    if largest_weight >= 0.30 or hhi >= 0.25 or effective_n < 3.0:
        return "Moderate concentration"
    return "Lower concentration"


def build_portfolio_risk(
    holdings: list[dict[str, Any]],
    benchmark: str = "^NSEI",
    period: str = "1y",
) -> dict[str, Any]:
    """Build descriptive portfolio risk and diversification evidence.

    No price forecasts or buy/sell recommendations are produced.
    """
    rows = _normalise_holdings(holdings)
    if not rows:
        return {"status": "empty", "message": "Add holdings with refreshed current prices first."}

    frame = pd.DataFrame(rows)
    frame["Current Value"] = frame["Quantity"] * frame["Current Price"]
    total_value = float(frame["Current Value"].sum())
    if total_value <= 0:
        return {"status": "empty", "message": "Portfolio current value is unavailable."}

    frame["Weight"] = frame["Current Value"] / total_value
    frame = frame.sort_values("Weight", ascending=False).reset_index(drop=True)

    weights = frame.set_index("Ticker")["Weight"]
    hhi = float((weights ** 2).sum())
    effective_n = float(1.0 / hhi) if hhi > 0 else None
    largest = float(frame.iloc[0]["Weight"])

    tickers = frame["Ticker"].tolist()
    prices = _download_prices(tickers, period=period)

    benchmark_prices = _download_prices([benchmark], period=period)
    benchmark_series = benchmark_prices[benchmark] if benchmark in benchmark_prices.columns else None
    returns = prices.pct_change(fill_method=None).dropna(how="all") if not prices.empty else pd.DataFrame()
    benchmark_returns = benchmark_series.pct_change(fill_method=None).dropna() if benchmark_series is not None else None

    stock_metrics: list[dict[str, Any]] = []
    for ticker in tickers:
        if ticker not in prices.columns:
            stock_metrics.append({"Ticker": ticker, "Volatility": None, "Max Drawdown": None, "Beta": None})
            continue
        series = prices[ticker].dropna()
        stock_ret = returns[ticker].dropna() if ticker in returns.columns else pd.Series(dtype=float)
        stock_metrics.append(
            {
                "Ticker": ticker,
                "Volatility": _annualised_volatility(stock_ret),
                "Max Drawdown": _max_drawdown(series),
                "Beta": _beta(stock_ret, benchmark_returns) if benchmark_returns is not None else None,
            }
        )

    metrics = pd.DataFrame(stock_metrics)

    common_returns = returns[[t for t in tickers if t in returns.columns]].dropna(how="all") if not returns.empty else pd.DataFrame()
    corr = common_returns.corr(min_periods=30) if not common_returns.empty else pd.DataFrame()

    avg_corr = None
    if len(corr.columns) >= 2:
        values = corr.values[np.triu_indices_from(corr.values, k=1)]
        values = values[np.isfinite(values)]
        if len(values):
            avg_corr = float(values.mean())

    portfolio_vol = None
    portfolio_beta = None
    risk_contrib = None
    if not common_returns.empty:
        usable = [t for t in tickers if t in common_returns.columns]
        if usable:
            aligned = common_returns[usable].dropna()
            if len(aligned) >= 30:
                w = frame.set_index("Ticker").loc[usable, "Weight"].to_numpy(dtype=float)
                cov = aligned.cov().to_numpy(dtype=float) * 252.0
                variance = float(w.T @ cov @ w)
                if variance > 0:
                    portfolio_vol = float(np.sqrt(variance))
                    marginal = cov @ w
                    contribution = w * marginal / variance
                    risk_contrib = pd.DataFrame(
                        {
                            "Ticker": usable,
                            "Portfolio Weight": w,
                            "Risk Contribution": contribution,
                        }
                    ).sort_values("Risk Contribution", ascending=False)

    if portfolio_beta is None and benchmark_returns is not None and not common_returns.empty:
        joined = common_returns.copy()
        common_benchmark = benchmark_returns.reindex(joined.index)
        joined["_portfolio"] = sum(joined[t].fillna(0) * frame.set_index("Ticker").loc[t, "Weight"] for t in usable)
        portfolio_beta = _beta(joined["_portfolio"], common_benchmark)

    concentration_level = _risk_level(largest, hhi, effective_n or 0)

    if len(tickers) == 1:
        diversification_note = "Diversification cannot be assessed from a single holding. Add at least one more holding to measure cross-holding correlation and risk contribution."
    elif avg_corr is None:
        diversification_note = "Multiple holdings are present, but there is not enough overlapping price history to calculate reliable pairwise correlation."
    elif avg_corr >= 0.70:
        diversification_note = "Holdings have high average correlation over the selected history, so they have tended to move together."
    elif avg_corr >= 0.40:
        diversification_note = "Holdings have moderate average correlation over the selected history."
    else:
        diversification_note = "Holdings have lower average correlation over the selected history, providing more variation in historical return patterns."

    return {
        "status": "ok",
        "holding_count": len(tickers),
        "total_value": total_value,
        "largest_holding": frame.iloc[0]["Ticker"],
        "largest_weight": largest,
        "hhi": hhi,
        "effective_number": effective_n,
        "concentration_level": concentration_level,
        "portfolio_volatility": portfolio_vol,
        "portfolio_beta": portfolio_beta,
        "average_correlation": avg_corr,
        "stock_metrics": metrics,
        "risk_contribution": risk_contrib,
        "correlation": corr,
        "diversification_note": diversification_note,
        "period": period,
        "benchmark": benchmark,
    }
