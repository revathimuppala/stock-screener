from functools import lru_cache
from pathlib import Path

from screener.application.analytics_cache import AnalyticsCache
from screener.application.backtest_service import BacktestService
from screener.application.company_detail_service import CompanyDetailService
from screener.application.financials_enrichment_stage import FinancialsEnrichmentStage
from screener.application.ports import (
    FilingLinkProvider,
    FinancialsProvider,
    MarketConstituentsProvider,
    PriceHistoryProvider,
    StockDataProvider,
)
from screener.application.saved_screen_service import SavedScreenService
from screener.application.screening_service import ScreeningService
from screener.application.technical_filter_stage import TechnicalFilterStage
from screener.application.watchlist_service import WatchlistService
from screener.domain.universe import UNIVERSE
from screener.infrastructure.backtest_job_store import BacktestJobStore
from screener.infrastructure.file_cached_market_constituents_provider import (
    FileCachedMarketConstituentsProvider,
)
from screener.infrastructure.file_cached_price_history_provider import FileCachedPriceHistoryProvider
from screener.infrastructure.market_constituents_provider import LiveMarketConstituentsProvider
from screener.infrastructure.resilient_financials_provider import ResilientFinancialsProvider
from screener.infrastructure.resilient_price_history_provider import ResilientPriceHistoryProvider
from screener.infrastructure.resilient_provider import ResilientStockDataProvider
from screener.infrastructure.sec_edgar_client import SecEdgarClient
from screener.infrastructure.sqlite_saved_screen_repository import SqliteSavedScreenRepository
from screener.infrastructure.sqlite_watchlist_repository import SqliteWatchlistRepository
from screener.infrastructure.treasury_yield_provider import TreasuryYieldProvider
from screener.infrastructure.yfinance_financials_provider import YFinanceFinancialsProvider
from screener.infrastructure.yfinance_price_history_provider import YFinancePriceHistoryProvider
from screener.infrastructure.yfinance_provider import YFinanceProvider

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@lru_cache
def get_treasury_yield_provider() -> TreasuryYieldProvider:
    """A single shared instance so its 1h in-memory cache is actually
    reused across every symbol fetch, not rebuilt per Ticker."""
    return TreasuryYieldProvider()


@lru_cache
def get_financials_provider() -> FinancialsProvider:
    """Composition root for balance-sheet/quarterly-statement/holders data:
    yfinance -> retry/breaker -> long-TTL in-memory cache."""
    return ResilientFinancialsProvider(inner=YFinanceFinancialsProvider())


@lru_cache
def get_stock_data_provider() -> StockDataProvider:
    """A single shared resilient provider so its retry/breaker/quote cache
    is reused by both screening and the company-detail view, rather than
    each building its own (and its own circuit breaker state)."""
    return ResilientStockDataProvider(
        fetcher=YFinanceProvider(treasury_yield_provider=get_treasury_yield_provider())
    )


@lru_cache
def get_filing_link_provider() -> FilingLinkProvider:
    """Composition root for SEC filing links. Cached so the in-memory
    ticker->CIK map (fetched once) is actually reused across requests."""
    return SecEdgarClient()


@lru_cache
def get_screening_service() -> ScreeningService:
    """Composition root for the screener: wires the resilient provider (with
    its own retry/breaker/cache) behind the ScreeningService's port, plus
    the technical and financials enrichment stages. Cached so the circuit
    breaker and quote cache are shared across requests."""
    return ScreeningService(
        provider=get_stock_data_provider(),
        universe=UNIVERSE,
        technical_filter_stage=TechnicalFilterStage(analytics_cache=get_analytics_cache()),
        financials_enrichment_stage=FinancialsEnrichmentStage(
            financials_provider=get_financials_provider()
        ),
    )


@lru_cache
def get_company_detail_service() -> CompanyDetailService:
    """Composition root for the company-detail drill-in view: shared stock
    provider + financials provider + SEC filing-link client."""
    return CompanyDetailService(
        stock_data_provider=get_stock_data_provider(),
        financials_provider=get_financials_provider(),
        filing_link_provider=get_filing_link_provider(),
    )


@lru_cache
def get_price_history_provider() -> PriceHistoryProvider:
    """Composition root for historical prices: yfinance -> retry/breaker ->
    on-disk incremental cache (data/returns/<SYMBOL>/returns.csv)."""
    resilient = ResilientPriceHistoryProvider(inner=YFinancePriceHistoryProvider())
    return FileCachedPriceHistoryProvider(inner=resilient, data_dir=_DATA_DIR / "returns")


@lru_cache
def get_analytics_cache() -> AnalyticsCache:
    """Composition root for derived technical indicators, backed by
    data/analytics/<SYMBOL>/<yyyymmdd>.csv."""
    return AnalyticsCache(price_history=get_price_history_provider(), data_dir=_DATA_DIR / "analytics")


@lru_cache
def get_watchlist_service() -> WatchlistService:
    """Composition root for the watchlist: wires the SQLite repository
    behind the WatchlistService's port. Cached so all requests share one
    engine/connection."""
    repository = SqliteWatchlistRepository()
    return WatchlistService(repository=repository)


@lru_cache
def get_saved_screen_service() -> SavedScreenService:
    """Composition root for saved screens: wires the SQLite repository
    behind the SavedScreenService's port."""
    repository = SqliteSavedScreenRepository()
    return SavedScreenService(repository=repository)


@lru_cache
def get_backtest_service() -> BacktestService:
    """Composition root for backtesting: a fresh resilient StockDataProvider
    (frozen fundamentals) plus the shared price history provider (real
    historical closes, file-cached)."""
    provider = ResilientStockDataProvider(
        fetcher=YFinanceProvider(treasury_yield_provider=get_treasury_yield_provider())
    )
    return BacktestService(
        stock_provider=provider,
        price_history_provider=get_price_history_provider(),
        universe=UNIVERSE,
    )


@lru_cache
def get_backtest_job_store() -> BacktestJobStore:
    """Composition root for backtest job records: data/backtesting/<uuid>.json."""
    return BacktestJobStore(data_dir=_DATA_DIR / "backtesting")


@lru_cache
def get_market_constituents_provider() -> MarketConstituentsProvider:
    """Composition root for market/index constituent lists: live fetch (S&P
    500 CSV, NASDAQ-100 Wikipedia, NSE500 CSV, BSE500 + Yahoo-search symbol
    resolution) -> long-TTL file cache (data/markets/<market_id>.json)."""
    return FileCachedMarketConstituentsProvider(
        inner=LiveMarketConstituentsProvider(), data_dir=_DATA_DIR / "markets"
    )


@lru_cache
def get_screen_job_store() -> BacktestJobStore:
    """Composition root for async screen-job records: data/screening/<uuid>.json.
    Reuses BacktestJobStore as-is — it's already a fully generic "JSON blob
    per uuid" store with nothing backtest-specific in it."""
    return BacktestJobStore(data_dir=_DATA_DIR / "screening")
