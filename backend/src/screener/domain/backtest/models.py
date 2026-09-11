from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class BacktestMatch:
    """A symbol that satisfied the matcher on a specific historical
    trading day, at that day's real closing price."""

    symbol: str
    match_date: date
    match_price: float


@dataclass(frozen=True, slots=True)
class BacktestPerformance:
    """What would have happened if you'd bought at the match and held for
    the requested number of days. `status` is "pending" when the holding
    period runs past the data we have (not yet excluded — just not over
    yet), never a made-up number."""

    match: BacktestMatch
    exit_date: date | None
    exit_price: float | None
    return_pct: float | None
    status: str  # "completed" | "pending"


@dataclass(frozen=True, slots=True)
class BacktestSummary:
    total_matches: int
    completed_count: int
    pending_count: int
    avg_return_pct: float | None
    win_rate: float | None
    best_return_pct: float | None
    worst_return_pct: float | None


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """The full record of one backtest run — also what gets persisted to
    data/backtesting/<uuid>.json as the job progresses."""

    status: str  # "pending" | "running" | "completed" | "failed"
    timeline: list[BacktestMatch]
    performances: list[BacktestPerformance]
    summary: BacktestSummary | None
    excluded_symbols: list[str]
    warnings: list[str]
    fundamentals_as_of: datetime | None
    error: str | None = None
