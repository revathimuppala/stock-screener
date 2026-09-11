from functools import lru_cache

from screener.application.screening_service import ScreeningService
from screener.application.watchlist_service import WatchlistService
from screener.domain.universe import UNIVERSE
from screener.infrastructure.resilient_provider import ResilientStockDataProvider
from screener.infrastructure.sqlite_watchlist_repository import SqliteWatchlistRepository
from screener.infrastructure.yfinance_provider import YFinanceProvider


@lru_cache
def get_screening_service() -> ScreeningService:
    """Composition root for the screener: wires the resilient provider (with
    its own retry/breaker/cache) behind the ScreeningService's port. Cached
    so the circuit breaker and quote cache are shared across requests."""
    provider = ResilientStockDataProvider(fetcher=YFinanceProvider())
    return ScreeningService(provider=provider, universe=UNIVERSE)


@lru_cache
def get_watchlist_service() -> WatchlistService:
    """Composition root for the watchlist: wires the SQLite repository
    behind the WatchlistService's port. Cached so all requests share one
    engine/connection."""
    repository = SqliteWatchlistRepository()
    return WatchlistService(repository=repository)
