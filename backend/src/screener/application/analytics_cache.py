from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from screener.application.ports import PriceHistoryProvider

_SMA_WINDOWS = (50, 100, 200)
_RSI_PERIOD = 14
_LOOKBACK_BUFFER_DAYS = 60  # covers weekends/holidays for a 200-trading-day window


@dataclass(frozen=True, slots=True)
class DailyAnalytics:
    symbol: str
    date: date
    sma_50: float | None = None
    sma_100: float | None = None
    sma_200: float | None = None
    rsi_14: float | None = None


def _sma(closes: list[float], window: int) -> float | None:
    if len(closes) < window:
        return None
    return sum(closes[-window:]) / window


def _rsi(closes: list[float], period: int = _RSI_PERIOD) -> float | None:
    """Standard Wilder's-smoothing RSI. Needs at least `period + 1` closes
    to seed the first average; every close beyond that further smooths the
    running average (Wilder's method, not a plain rolling window)."""
    if len(closes) < period + 1:
        return None

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    if avg_gain == 0:
        return 0.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


class AnalyticsCache:
    """Given (symbol, date), returns derived technical indicators for that
    day — computing them from price history on first request. A *past*
    trading day's analytics never change once computed, so those are
    persisted permanently to `data_dir/<SYMBOL>/<yyyymmdd>.csv`; today's
    (or any non-past date's) analytics are always recomputed and never
    written, since the underlying data for that day can still move.
    Shared by the screener's technical enrichment/filters and backtest
    snapshot reconstruction, so a live filter and a backtest can never
    disagree about what a symbol's SMA/RSI was on a given date."""

    def __init__(self, price_history: PriceHistoryProvider, data_dir: Path):
        self._price_history = price_history
        self._data_dir = data_dir

    def get(self, symbol: str, on_date: date) -> DailyAnalytics:
        is_past = on_date < date.today()
        path = self._csv_path(symbol, on_date)
        if is_past and path.exists():
            return self._read(path, symbol, on_date)

        analytics = self._compute(symbol, on_date)
        if is_past:
            self._write(path, analytics)
        return analytics

    def _compute(self, symbol: str, on_date: date) -> DailyAnalytics:
        lookback_start = on_date - timedelta(days=max(_SMA_WINDOWS) * 7 // 5 + _LOOKBACK_BUFFER_DAYS)
        bars = self._price_history.get_history(symbol, lookback_start, on_date)
        closes = [b.close for b in bars if b.date <= on_date]
        return DailyAnalytics(
            symbol=symbol,
            date=on_date,
            sma_50=_sma(closes, 50),
            sma_100=_sma(closes, 100),
            sma_200=_sma(closes, 200),
            rsi_14=_rsi(closes),
        )

    def _csv_path(self, symbol: str, on_date: date) -> Path:
        return self._data_dir / symbol / f"{on_date.strftime('%Y%m%d')}.csv"

    def _read(self, path: Path, symbol: str, on_date: date) -> DailyAnalytics:
        with path.open(newline="") as f:
            row = next(csv.DictReader(f))
        return DailyAnalytics(
            symbol=symbol,
            date=on_date,
            sma_50=float(row["sma_50"]) if row["sma_50"] else None,
            sma_100=float(row["sma_100"]) if row["sma_100"] else None,
            sma_200=float(row["sma_200"]) if row["sma_200"] else None,
            rsi_14=float(row["rsi_14"]) if row["rsi_14"] else None,
        )

    def _write(self, path: Path, analytics: DailyAnalytics) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["sma_50", "sma_100", "sma_200", "rsi_14"])
            writer.writerow(
                [
                    analytics.sma_50 or "",
                    analytics.sma_100 or "",
                    analytics.sma_200 or "",
                    analytics.rsi_14 or "",
                ]
            )
