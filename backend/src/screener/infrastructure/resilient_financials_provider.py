from __future__ import annotations

from screener.application.ports import FinancialsProvider
from screener.domain.entities import RawFinancials
from screener.infrastructure.resilience import ResilientFetcher

_SIX_HOURS = 6 * 3600  # financials change quarterly — a long TTL is correct


class ResilientFinancialsProvider:
    """Adds timeout-bounded retry + circuit breaker + a long-TTL cache
    (via the shared ResilientFetcher — financials don't need the file-cache
    machinery built for daily prices, an in-memory TTL is enough) around a
    raw FinancialsProvider."""

    def __init__(self, inner: FinancialsProvider, **resilience_kwargs):
        resilience_kwargs.setdefault("cache_ttl_seconds", _SIX_HOURS)
        self._resilient: ResilientFetcher[RawFinancials] = ResilientFetcher(
            fetch_one=inner.get_financials,
            mark_stale=lambda financials: financials,  # no staleness concept for statements
            **resilience_kwargs,
        )

    def get_financials(self, symbol: str) -> RawFinancials | None:
        return self._resilient.resolve(symbol)
