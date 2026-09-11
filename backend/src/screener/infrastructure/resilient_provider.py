from __future__ import annotations

from dataclasses import replace
from typing import Protocol

import pybreaker
from cachetools import TTLCache
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from screener.application.ports import ProviderBatchResult
from screener.domain.entities import Stock
from screener.infrastructure.exceptions import ProviderError, TransientProviderError


class SingleSymbolFetcher(Protocol):
    """The narrow, low-level thing a resiliency wrapper needs: fetch one
    symbol or raise. Kept separate from the batch-oriented StockDataProvider
    port so the retry/breaker/cache logic operates at the grain it actually
    needs (ISP) — a raw adapter like YFinanceProvider only has to implement
    this one method."""

    def fetch(self, symbol: str) -> Stock: ...


class ResilientStockDataProvider:
    """Wraps a SingleSymbolFetcher with timeout-bounded retry, a circuit
    breaker, and a stale-cache fallback, and exposes the batch-oriented
    StockDataProvider port the application layer depends on. All resiliency
    policy lives here, once — see specs/resiliency.md."""

    def __init__(
        self,
        fetcher: SingleSymbolFetcher,
        retry_attempts: int = 3,
        retry_wait_seconds: float = 0.5,
        breaker_fail_max: int = 5,
        breaker_reset_seconds: float = 30,
        cache_ttl_seconds: float = 3600,
    ):
        self._fetcher = fetcher
        self._retry_attempts = retry_attempts
        self._retry_wait_seconds = retry_wait_seconds
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=breaker_fail_max, reset_timeout=breaker_reset_seconds
        )
        self._cache: TTLCache[str, Stock] = TTLCache(maxsize=512, ttl=cache_ttl_seconds)

    def get_quotes(self, symbols: list[str]) -> ProviderBatchResult:
        stocks: list[Stock] = []
        excluded_symbols: list[str] = []
        for symbol in symbols:
            stock = self._resolve(symbol)
            if stock is None:
                excluded_symbols.append(symbol)
            else:
                stocks.append(stock)
        return ProviderBatchResult(stocks=stocks, excluded_symbols=excluded_symbols)

    def _resolve(self, symbol: str) -> Stock | None:
        try:
            stock = self._breaker.call(self._fetch_with_retry, symbol)
        except (pybreaker.CircuitBreakerError, ProviderError):
            return self._serve_stale_from_cache(symbol)
        self._cache[symbol] = stock
        return stock

    def _fetch_with_retry(self, symbol: str) -> Stock:
        retrying = Retrying(
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_fixed(self._retry_wait_seconds),
            retry=retry_if_exception_type(TransientProviderError),
            reraise=True,
        )
        return retrying(self._fetcher.fetch, symbol)

    def _serve_stale_from_cache(self, symbol: str) -> Stock | None:
        cached = self._cache.get(symbol)
        if cached is None:
            return None
        return replace(cached, is_stale=True)
