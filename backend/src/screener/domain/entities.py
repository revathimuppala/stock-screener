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
    peg_ratio: float | None = None
    ev_to_ebitda: float | None = None
    operating_margin: float | None = None
    # Total Debt / Total Assets — distinct from debt_to_equity above; needs
    # the balance sheet (YFinanceFinancialsProvider), not the quote info.
    debt_to_assets: float | None = None
    # OperatingCashFlow / EBIT for the latest reported quarter.
    cfo_to_operating_profit: float | None = None
    # Computed estimates (domain/valuation.py) — not filterable, see
    # ScreeningCriteria: these are outputs of a model, not raw data to
    # screen on.
    graham_value: float | None = None
    dcf_value: float | None = None
    # Populated by TechnicalAnalysisStage.enrich() on every screen result,
    # not just when filtering — see application/technical_filter_stage.py.
    sma_50: float | None = None
    sma_100: float | None = None
    sma_200: float | None = None
    rsi_14: float | None = None
    # Used by CompanyDetailService for the business summary and
    # industry-peer competitor lookup — not shown in the screener table.
    industry: str | None = None
    business_summary: str | None = None


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
    above_sma_window: int | None = None  # 50, 100, or 200
    peg_ratio_max: float | None = None
    ev_to_ebitda_max: float | None = None
    operating_margin_min: float | None = None
    debt_to_assets_max: float | None = None
    cfo_to_operating_profit_min: float | None = None
    rsi_min: float | None = None
    rsi_max: float | None = None
    # Screen this explicit symbol list instead of the default universe.
    symbols: list[str] | None = None


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
class QuarterlyFinancials:
    """One quarter's financial highlights — a curated subset of the full
    statements, not a raw dump (see specs/company_detail.md)."""

    period_end: date
    revenue: float | None
    ebit: float | None
    ebitda: float | None
    net_income: float | None
    diluted_eps: float | None
    operating_cash_flow: float | None
    free_cash_flow: float | None


@dataclass(frozen=True, slots=True)
class InstitutionalHolder:
    name: str
    value: float | None
    pct_change: float | None


@dataclass(frozen=True, slots=True)
class ShareholdingPattern:
    insiders_pct: float | None
    institutions_pct: float | None
    top_holders: list[InstitutionalHolder]


@dataclass(frozen=True, slots=True)
class RawFinancials:
    """Everything FinancialsProvider fetches for one symbol in a single
    round trip — balance-sheet totals (for debt_to_assets), quarterly
    highlights (for cfo_to_operating_profit and the company-detail view),
    and the shareholding pattern. Bundled together so Stock enrichment and
    the company-detail endpoint never re-fetch the same statements."""

    symbol: str
    total_debt: float | None
    total_assets: float | None
    quarters: list[QuarterlyFinancials]  # most recent first
    shareholding: ShareholdingPattern | None


@dataclass(frozen=True, slots=True)
class FilingLink:
    """One SEC filing — the latest of its type, not a full history (see
    SecEdgarClient)."""

    form_type: str  # "10-K", "10-Q", or "DEF 14A"
    filed_date: date
    url: str


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    business_summary: str | None
    sector: str
    industry: str | None
    competitors: list[str]  # other UNIVERSE symbols sharing `industry`
    # Order backlog isn't available as structured data from any free
    # source — always this note (pointing at the real filing) rather than
    # a fabricated number. See specs/company_detail.md.
    order_backlog_note: str


@dataclass(frozen=True, slots=True)
class CompanyDetail:
    symbol: str
    profile: CompanyProfile
    quarters: list[QuarterlyFinancials]
    shareholding: ShareholdingPattern | None
    filings: list[FilingLink]


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
