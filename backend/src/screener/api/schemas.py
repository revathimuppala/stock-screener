from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, model_validator


class ScreenRequest(BaseModel):
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
    above_sma_window: int | None = None


class StockResponse(BaseModel):
    symbol: str
    name: str
    sector: str
    price: float
    pe_ratio: float | None
    market_cap: float | None
    dividend_yield: float | None
    is_stale: bool
    roe: float | None = None
    debt_to_equity: float | None = None
    price_to_book: float | None = None
    earnings_growth: float | None = None
    revenue_growth: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None


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


class SaveScreenRequest(BaseModel):
    name: str
    criteria: ScreenRequest | None = None
    query: str | None = None

    @model_validator(mode="after")
    def exactly_one_of_criteria_or_query(self) -> "SaveScreenRequest":
        if (self.criteria is None) == (self.query is None):
            raise ValueError("Exactly one of criteria or query must be provided")
        return self


class SavedScreenResponse(BaseModel):
    id: str
    name: str
    criteria: ScreenRequest | None
    query: str | None
    created_at: datetime


class SavedScreenListResponse(BaseModel):
    screens: list[SavedScreenResponse]


class QueryRequest(BaseModel):
    query: str


class BacktestRequest(BaseModel):
    criteria: ScreenRequest | None = None
    query: str | None = None
    start_date: date
    end_date: date
    holding_period_days: int

    @model_validator(mode="after")
    def exactly_one_of_criteria_or_query(self) -> "BacktestRequest":
        if (self.criteria is None) == (self.query is None):
            raise ValueError("Exactly one of criteria or query must be provided")
        return self


class BacktestStartResponse(BaseModel):
    backtest_id: str
    status: str
