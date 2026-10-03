from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


class SQLiteCache:
    """Local SQLite cache for downloaded market data."""

    def __init__(
        self,
        database_path: str = "investiq_cache.db",
        ttl_hours: int = 24,
    ) -> None:
        self.database_path = Path(database_path)
        self.ttl = timedelta(hours=ttl_hours)
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS price_cache (
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    cached_at TEXT NOT NULL,
                    PRIMARY KEY (ticker, date)
                )
                """
            )
            connection.commit()

    def save(self, ticker: str, data: pd.DataFrame) -> None:
        if data.empty:
            return

        now = datetime.utcnow().isoformat()

        with self._connect() as connection:
            for timestamp, row in data.iterrows():
                connection.execute(
                    """
                    INSERT OR REPLACE INTO price_cache
                    (
                        ticker,
                        date,
                        open,
                        high,
                        low,
                        close,
                        volume,
                        cached_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ticker,
                        timestamp.strftime("%Y-%m-%d"),
                        float(row["Open"]),
                        float(row["High"]),
                        float(row["Low"]),
                        float(row["Close"]),
                        float(row["Volume"]),
                        now,
                    ),
                )

            connection.commit()

    def load(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        cutoff = datetime.utcnow() - self.ttl

        with self._connect() as connection:
            query = """
                SELECT
                    date,
                    open,
                    high,
                    low,
                    close,
                    volume
                FROM price_cache
                WHERE ticker = ?
                  AND date >= ?
                  AND date <= ?
                  AND cached_at >= ?
                ORDER BY date
            """

            rows = connection.execute(
                query,
                (
                    ticker,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                    cutoff.isoformat(),
                ),
            ).fetchall()

        if not rows:
            return pd.DataFrame()

        data = pd.DataFrame(
            rows,
            columns=[
                "date",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ],
        )

        data["date"] = pd.to_datetime(data["date"])
        data = data.set_index("date")

        return data

    def clear(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM price_cache")
            connection.commit()