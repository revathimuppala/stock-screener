from __future__ import annotations

from screener.domain.dsl.matcher import DslMatcher
from screener.domain.entities import ScreeningCriteria
from screener.domain.filters import FilterChain
from screener.domain.matcher import Matcher


class UnsupportedQueryError(Exception):
    """Kept for backwards compatibility with callers that catch it
    specifically; DSL queries are now supported, so this no longer raises
    from build_matcher, but a malformed query still raises DslError."""


def build_matcher(criteria: ScreeningCriteria | None, query: str | None) -> Matcher:
    """Builds a Matcher from either structured criteria or a DSL query
    string — the one place that knows how to turn either shape into
    something ScreeningService/BacktestService can run against a Stock."""
    if (criteria is None) == (query is None):
        raise ValueError("Exactly one of criteria or query must be provided")
    if criteria is not None:
        return FilterChain.from_criteria(criteria)
    assert query is not None
    return DslMatcher(query)
