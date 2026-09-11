from __future__ import annotations

from dataclasses import replace
from datetime import date

from screener.application.analytics_cache import AnalyticsCache
from screener.domain.entities import Stock

_SUPPORTED_WINDOWS = (50, 100, 200)


class TechnicalFilterStage:
    """Two responsibilities, both backed by AnalyticsCache: `enrich()`
    attaches SMA/RSI to every stock in a result set for display (called
    once per screen, regardless of whether any technical criterion was
    given), and `apply`/`filter_by_rsi` narrow an already-enriched set by
    a technical criterion. Deliberately separate from FilterChain (which
    stays pure/sync, no I/O) — these need price history."""

    def __init__(self, analytics_cache: AnalyticsCache):
        self._analytics_cache = analytics_cache

    def enrich(self, stocks: list[Stock]) -> list[Stock]:
        today = date.today()
        enriched = []
        for stock in stocks:
            analytics = self._analytics_cache.get(stock.symbol, today)
            enriched.append(
                replace(
                    stock,
                    sma_50=analytics.sma_50,
                    sma_100=analytics.sma_100,
                    sma_200=analytics.sma_200,
                    rsi_14=analytics.rsi_14,
                )
            )
        return enriched

    def apply(self, stocks: list[Stock], above_sma_window: int) -> list[Stock]:
        if above_sma_window not in _SUPPORTED_WINDOWS:
            raise ValueError(f"Unsupported SMA window: {above_sma_window}. Supported: {_SUPPORTED_WINDOWS}")

        today = date.today()
        result = []
        for stock in stocks:
            analytics = self._analytics_cache.get(stock.symbol, today)
            sma = {50: analytics.sma_50, 100: analytics.sma_100, 200: analytics.sma_200}[above_sma_window]
            if sma is not None and stock.price > sma:
                result.append(stock)
        return result

    def filter_by_rsi(self, stocks: list[Stock], rsi_min: float | None, rsi_max: float | None) -> list[Stock]:
        today = date.today()
        result = []
        for stock in stocks:
            rsi = self._analytics_cache.get(stock.symbol, today).rsi_14
            if rsi is None:
                continue
            if rsi_min is not None and rsi < rsi_min:
                continue
            if rsi_max is not None and rsi > rsi_max:
                continue
            result.append(stock)
        return result
