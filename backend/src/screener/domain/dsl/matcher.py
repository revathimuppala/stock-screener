from __future__ import annotations

from screener.domain.dsl.evaluator import evaluate
from screener.domain.dsl.parser import parse
from screener.domain.entities import Stock


class DslMatcher:
    """Wraps a parsed DSL query behind the same Matcher shape as
    FilterChain — parses once at construction (so a bad query fails fast,
    before ever touching data), evaluates per Stock thereafter."""

    def __init__(self, query: str):
        self._expression = parse(query)

    def matches(self, stock: Stock) -> bool:
        return evaluate(self._expression, stock)
