from __future__ import annotations

from datetime import date

from screener.application.analytics_cache import AnalyticsCache
from screener.domain.entities import Stock

_SUPPORTED_WINDOWS = (50, 200)


class TechnicalFilterStage:
    """Filters by "price above its N-day SMA" — deliberately separate
    from FilterChain (which stays pure/sync, no I/O). Runs after
    FilterChain, over whatever subset already passed the fundamental
    filters, to minimize AnalyticsCache/PriceHistoryProvider calls."""

    def __init__(self, analytics_cache: AnalyticsCache):
        self._analytics_cache = analytics_cache

    def apply(self, stocks: list[Stock], above_sma_window: int) -> list[Stock]:
        if above_sma_window not in _SUPPORTED_WINDOWS:
            raise ValueError(f"Unsupported SMA window: {above_sma_window}. Supported: {_SUPPORTED_WINDOWS}")

        today = date.today()
        result = []
        for stock in stocks:
            analytics = self._analytics_cache.get(stock.symbol, today)
            sma = analytics.sma_50 if above_sma_window == 50 else analytics.sma_200
            if sma is not None and stock.price > sma:
                result.append(stock)
        return result
