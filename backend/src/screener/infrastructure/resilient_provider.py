from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from screener.application.ports import ProviderBatchResult
from screener.domain.entities import Stock
from screener.infrastructure.resilience import ResilientFetcher


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
    StockDataProvider port the application layer depends on. Resiliency
    policy itself lives in ResilientFetcher (shared with other per-symbol
    providers, e.g. price history) — see specs/resiliency.md."""

    def __init__(
        self,
        fetcher: SingleSymbolFetcher,
        retry_attempts: int = 3,
        retry_wait_seconds: float = 0.5,
        breaker_fail_max: int = 5,
        breaker_reset_seconds: float = 30,
        cache_ttl_seconds: float = 3600,
    ):
        self._resilient: ResilientFetcher[Stock] = ResilientFetcher(
            fetch_one=fetcher.fetch,
            mark_stale=lambda stock: replace(stock, is_stale=True),
            retry_attempts=retry_attempts,
            retry_wait_seconds=retry_wait_seconds,
            breaker_fail_max=breaker_fail_max,
            breaker_reset_seconds=breaker_reset_seconds,
            cache_ttl_seconds=cache_ttl_seconds,
        )

    def get_quotes(self, symbols: list[str]) -> ProviderBatchResult:
        stocks: list[Stock] = []
        excluded_symbols: list[str] = []
        for symbol in symbols:
            stock = self._resilient.resolve(symbol)
            if stock is None:
                excluded_symbols.append(symbol)
            else:
                stocks.append(stock)
        return ProviderBatchResult(stocks=stocks, excluded_symbols=excluded_symbols)
