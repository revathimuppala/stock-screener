from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ScreenRequest(BaseModel):
    pe_min: float | None = None
    pe_max: float | None = None
    market_cap_min: float | None = None
    market_cap_max: float | None = None
    sector: str | None = None
    min_dividend_yield: float | None = None


class StockResponse(BaseModel):
    symbol: str
    name: str
    sector: str
    price: float
    pe_ratio: float | None
    market_cap: float | None
    dividend_yield: float | None
    is_stale: bool


class ScreenResponse(BaseModel):
    status: str
    results: list[StockResponse]
    stale_symbols: list[str]
    excluded_symbols: list[str]
    as_of: datetime


class AddWatchlistSymbolRequest(BaseModel):
    symbol: str


class WatchlistResponse(BaseModel):
    symbols: list[str]
