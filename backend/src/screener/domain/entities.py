from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


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


@dataclass(frozen=True, slots=True)
class ScreeningCriteria:
    pe_min: float | None = None
    pe_max: float | None = None
    market_cap_min: float | None = None
    market_cap_max: float | None = None
    sector: str | None = None
    min_dividend_yield: float | None = None


@dataclass(frozen=True, slots=True)
class ScreeningResult:
    status: str  # "ok" | "degraded"
    results: list[Stock]
    stale_symbols: list[str]
    excluded_symbols: list[str]
    as_of: datetime
