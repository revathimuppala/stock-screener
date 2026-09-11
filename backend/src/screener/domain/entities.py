from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class Stock:
    symbol: str
    name: str
    sector: str
    price: float
    pe_ratio: float | None
    market_cap: float | None
    dividend_yield: float | None
    as_of: datetime
    is_stale: bool = False
    roe: float | None = None
    # Raw ratio as reported by the provider (e.g. 78.4 meaning debt is 78.4%
    # of equity) — NOT a 0-1 fraction like roe/dividend_yield. Verified
    # against a live call; don't assume unit parity with the other fields.
    debt_to_equity: float | None = None
    price_to_book: float | None = None
    earnings_growth: float | None = None
    revenue_growth: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None


@dataclass(frozen=True, slots=True)
class ScreeningCriteria:
    pe_min: float | None = None
    pe_max: float | None = None
    market_cap_min: float | None = None
    market_cap_max: float | None = None
    sector: str | None = None
    min_dividend_yield: float | None = None
    roe_min: float | None = None
    debt_to_equity_max: float | None = None
    price_to_book_max: float | None = None
    earnings_growth_min: float | None = None
    revenue_growth_min: float | None = None
    near_52_week_high_pct: float | None = None
    above_sma_window: int | None = None  # 50 or 200


@dataclass(frozen=True, slots=True)
class ScreeningResult:
    status: str  # "ok" | "degraded"
    results: list[Stock]
    stale_symbols: list[str]
    excluded_symbols: list[str]
    as_of: datetime


@dataclass(frozen=True, slots=True)
class PriceBar:
    """One trading day's closing price for a symbol."""

    date: date
    close: float


@dataclass(frozen=True, slots=True)
class SavedScreen:
    """A screen a user wants to re-run later. Exactly one of `criteria`
    (the structured form) or `query` (the DSL) is set — enforced by
    SavedScreenService, not here, so this stays a plain data holder."""

    id: str
    name: str
    criteria: ScreeningCriteria | None
    query: str | None
    created_at: datetime
