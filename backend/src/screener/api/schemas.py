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
    peg_ratio_max: float | None = None
    ev_to_ebitda_max: float | None = None
    operating_margin_min: float | None = None
    debt_to_assets_max: float | None = None
    cfo_to_operating_profit_min: float | None = None
    rsi_min: float | None = None
    rsi_max: float | None = None
    symbols: list[str] | None = None


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
    peg_ratio: float | None = None
    ev_to_ebitda: float | None = None
    operating_margin: float | None = None
    debt_to_assets: float | None = None
    cfo_to_operating_profit: float | None = None
    graham_value: float | None = None
    dcf_value: float | None = None
    sma_50: float | None = None
    sma_100: float | None = None
    sma_200: float | None = None
    rsi_14: float | None = None


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
    symbols: list[str] | None = None


class BacktestRequest(BaseModel):
    criteria: ScreenRequest | None = None
    query: str | None = None
    start_date: date
    end_date: date
    holding_period_days: int
    symbols: list[str] | None = None

    @model_validator(mode="after")
    def exactly_one_of_criteria_or_query(self) -> "BacktestRequest":
        if (self.criteria is None) == (self.query is None):
            raise ValueError("Exactly one of criteria or query must be provided")
        return self


class BacktestStartResponse(BaseModel):
    backtest_id: str
    status: str


class QuarterlyFinancialsResponse(BaseModel):
    period_end: date
    revenue: float | None
    ebit: float | None
    ebitda: float | None
    net_income: float | None
    diluted_eps: float | None
    operating_cash_flow: float | None
    free_cash_flow: float | None


class InstitutionalHolderResponse(BaseModel):
    name: str
    value: float | None
    pct_change: float | None


class ShareholdingPatternResponse(BaseModel):
    insiders_pct: float | None
    institutions_pct: float | None
    top_holders: list[InstitutionalHolderResponse]


class FilingLinkResponse(BaseModel):
    form_type: str
    filed_date: date
    url: str


class CompanyProfileResponse(BaseModel):
    business_summary: str | None
    sector: str
    industry: str | None
    competitors: list[str]
    order_backlog_note: str


class CompanyDetailResponse(BaseModel):
    symbol: str
    profile: CompanyProfileResponse
    quarters: list[QuarterlyFinancialsResponse]
    shareholding: ShareholdingPatternResponse | None
    filings: list[FilingLinkResponse]


class DslFieldResponse(BaseModel):
    name: str
    type: str  # "string" | "number"


class DslFieldsResponse(BaseModel):
    fields: list[DslFieldResponse]
    aliases: dict[str, str]


class MarketResponse(BaseModel):
    id: str
    label: str


class MarketsResponse(BaseModel):
    markets: list[MarketResponse]


class ScreenJobRequest(BaseModel):
    market_id: str
    criteria: ScreenRequest | None = None
    query: str | None = None
    symbols: list[str] | None = None

    @model_validator(mode="after")
    def exactly_one_of_criteria_or_query(self) -> "ScreenJobRequest":
        if (self.criteria is None) == (self.query is None):
            raise ValueError("Exactly one of criteria or query must be provided")
        return self


class ScreenJobStartResponse(BaseModel):
    screen_id: str
    status: str
