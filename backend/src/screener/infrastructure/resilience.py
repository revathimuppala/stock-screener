from __future__ import annotations

import threading
from typing import Callable, Generic, TypeVar

import pybreaker
from cachetools import TTLCache
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from screener.infrastructure.exceptions import ProviderError, TransientProviderError

T = TypeVar("T")


class ResilientFetcher(Generic[T]):
    """Generic timeout-bounded retry + circuit breaker + stale-cache
    fallback around a single-key fetch function. One resiliency policy,
    reused by any per-symbol provider (live quotes, price history, ...) —
    see specs/resiliency.md. `mark_stale` adapts a cached value into
    whatever "this came from cache, not a live call" looks like for that
    value's type (e.g. flipping `Stock.is_stale`); pass `lambda v: v` for
    types with no such concept."""

    def __init__(
        self,
        fetch_one: Callable[[str], T],
        mark_stale: Callable[[T], T],
        retry_attempts: int = 3,
        retry_wait_seconds: float = 0.5,
        breaker_fail_max: int = 5,
        breaker_reset_seconds: float = 30,
        cache_ttl_seconds: float = 3600,
    ):
        self._fetch_one = fetch_one
        self._mark_stale = mark_stale
        self._retry_attempts = retry_attempts
        self._retry_wait_seconds = retry_wait_seconds
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=breaker_fail_max, reset_timeout=breaker_reset_seconds
        )
        self._cache: TTLCache[str, T] = TTLCache(maxsize=512, ttl=cache_ttl_seconds)
        # cachetools.TTLCache isn't safe under concurrent mutation (its
        # expiry bookkeeping does more than a plain dict __setitem__) —
        # needed once callers start resolving many keys concurrently
        # (ResilientStockDataProvider.get_quotes uses a thread pool for
        # large market universes). pybreaker.CircuitBreaker is already
        # thread-safe internally, so it needs no lock here.
        self._cache_lock = threading.Lock()

    def resolve(self, key: str) -> T | None:
        try:
            value = self._breaker.call(self._fetch_with_retry, key)
        except (pybreaker.CircuitBreakerError, ProviderError):
            return self._serve_stale_from_cache(key)
        with self._cache_lock:
            self._cache[key] = value
        return value

    def _fetch_with_retry(self, key: str) -> T:
        retrying = Retrying(
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_fixed(self._retry_wait_seconds),
            retry=retry_if_exception_type(TransientProviderError),
            reraise=True,
        )
        return retrying(self._fetch_one, key)

    def _serve_stale_from_cache(self, key: str) -> T | None:
        with self._cache_lock:
            cached = self._cache.get(key)
        if cached is None:
            return None
        return self._mark_stale(cached)
