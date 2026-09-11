from functools import lru_cache
from pathlib import Path

from screener.application.analytics_cache import AnalyticsCache
from screener.application.backtest_service import BacktestService
from screener.application.ports import PriceHistoryProvider
from screener.application.saved_screen_service import SavedScreenService
from screener.application.screening_service import ScreeningService
from screener.application.technical_filter_stage import TechnicalFilterStage
from screener.application.watchlist_service import WatchlistService
from screener.domain.universe import UNIVERSE
from screener.infrastructure.backtest_job_store import BacktestJobStore
from screener.infrastructure.file_cached_price_history_provider import FileCachedPriceHistoryProvider
from screener.infrastructure.resilient_price_history_provider import ResilientPriceHistoryProvider
from screener.infrastructure.resilient_provider import ResilientStockDataProvider
from screener.infrastructure.sqlite_saved_screen_repository import SqliteSavedScreenRepository
from screener.infrastructure.sqlite_watchlist_repository import SqliteWatchlistRepository
from screener.infrastructure.yfinance_price_history_provider import YFinancePriceHistoryProvider
from screener.infrastructure.yfinance_provider import YFinanceProvider

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@lru_cache
def get_screening_service() -> ScreeningService:
    """Composition root for the screener: wires the resilient provider (with
    its own retry/breaker/cache) behind the ScreeningService's port, plus
    the technical filter stage for above_sma_window screens. Cached so the
    circuit breaker and quote cache are shared across requests."""
    provider = ResilientStockDataProvider(fetcher=YFinanceProvider())
    return ScreeningService(
        provider=provider,
        universe=UNIVERSE,
        technical_filter_stage=TechnicalFilterStage(analytics_cache=get_analytics_cache()),
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
    provider = ResilientStockDataProvider(fetcher=YFinanceProvider())
    return BacktestService(
        stock_provider=provider,
        price_history_provider=get_price_history_provider(),
        universe=UNIVERSE,
    )


@lru_cache
def get_backtest_job_store() -> BacktestJobStore:
    """Composition root for backtest job records: data/backtesting/<uuid>.json."""
    return BacktestJobStore(data_dir=_DATA_DIR / "backtesting")
