from __future__ import annotations

from datetime import date

from screener.application.ports import PriceHistoryProvider
from screener.domain.entities import PriceBar
from screener.infrastructure.resilience import ResilientFetcher


def _encode_key(symbol: str, start: date, end: date) -> str:
    return f"{symbol}|{start.isoformat()}|{end.isoformat()}"


def _decode_key(key: str) -> tuple[str, date, date]:
    symbol, start_str, end_str = key.split("|")
    return symbol, date.fromisoformat(start_str), date.fromisoformat(end_str)


class ResilientPriceHistoryProvider:
    """Adds timeout-bounded retry + circuit breaker (via the shared
    ResilientFetcher) around a raw PriceHistoryProvider. No stale-serving
    concept here (`mark_stale` is the identity) — bars are either fetched
    or not; FileCachedPriceHistoryProvider is the actual persistent cache
    layer, this only protects against transient failures within one call."""

    def __init__(self, inner: PriceHistoryProvider, **resilience_kwargs):
        self._resilient: ResilientFetcher[list[PriceBar]] = ResilientFetcher(
            fetch_one=lambda key: inner.get_history(*_decode_key(key)),
            mark_stale=lambda bars: bars,
            **resilience_kwargs,
        )

    def get_history(self, symbol: str, start: date, end: date) -> list[PriceBar]:
        bars = self._resilient.resolve(_encode_key(symbol, start, end))
        return bars if bars is not None else []
