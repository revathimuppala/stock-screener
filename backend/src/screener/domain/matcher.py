from __future__ import annotations

from typing import Protocol

from screener.domain.entities import Stock


class Matcher(Protocol):
    """Anything that can decide whether a Stock qualifies. FilterChain
    (structured criteria) and DslMatcher (query text) both satisfy this
    shape, which is what lets ScreeningService and BacktestService accept
    either without caring which one built it."""

    def matches(self, stock: Stock) -> bool: ...
