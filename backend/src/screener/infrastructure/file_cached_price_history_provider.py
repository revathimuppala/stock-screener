from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

from screener.application.ports import PriceHistoryProvider
from screener.domain.entities import PriceBar

_ONE_DAY = timedelta(days=1)


class FileCachedPriceHistoryProvider:
    """Wraps a raw PriceHistoryProvider with a per-symbol CSV cache at
    `data_dir/<SYMBOL>/returns.csv` — the same "decorate the raw adapter"
    pattern as ResilientStockDataProvider wrapping YFinanceProvider. Only
    the date range NOT already covered by the cache is ever fetched from
    the inner provider; everything else is served from disk."""

    def __init__(self, inner: PriceHistoryProvider, data_dir: Path):
        self._inner = inner
        self._data_dir = data_dir

    def get_history(self, symbol: str, start: date, end: date) -> list[PriceBar]:
        path = self._csv_path(symbol)
        cached = self._read_csv(path)

        new_bars: list[PriceBar] = []
        if not cached:
            new_bars = self._inner.get_history(symbol, start, end)
        else:
            cached_min = cached[0].date
            cached_max = cached[-1].date
            if start < cached_min:
                new_bars += self._inner.get_history(symbol, start, cached_min - _ONE_DAY)
            if end > cached_max:
                new_bars += self._inner.get_history(symbol, cached_max + _ONE_DAY, end)

        if new_bars:
            merged = {bar.date: bar for bar in cached}
            for bar in new_bars:
                merged[bar.date] = bar
            cached = sorted(merged.values(), key=lambda b: b.date)
            self._write_csv(path, cached)

        return [b for b in cached if start <= b.date <= end]

    def _csv_path(self, symbol: str) -> Path:
        return self._data_dir / symbol / "returns.csv"

    def _read_csv(self, path: Path) -> list[PriceBar]:
        if not path.exists():
            return []
        with path.open(newline="") as f:
            reader = csv.DictReader(f)
            return [
                PriceBar(date=date.fromisoformat(row["date"]), close=float(row["close"]))
                for row in reader
            ]

    def _write_csv(self, path: Path, bars: list[PriceBar]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "close", "daily_return_pct"])
            previous_close: float | None = None
            for bar in bars:
                daily_return = (bar.close / previous_close - 1) if previous_close else ""
                writer.writerow([bar.date.isoformat(), bar.close, daily_return])
                previous_close = bar.close
