from __future__ import annotations

from datetime import datetime, timezone

from screener.application.ports import StockDataProvider
from screener.application.technical_filter_stage import TechnicalFilterStage
from screener.domain.entities import ScreeningCriteria, ScreeningResult, Stock
from screener.domain.filters import FilterChain
from screener.domain.matcher import Matcher


def _rank_key(stock: Stock) -> tuple[float, float]:
    yield_desc = -(stock.dividend_yield or 0.0)
    pe_asc = stock.pe_ratio if stock.pe_ratio is not None else float("inf")
    return (yield_desc, pe_asc)


def _rerank_after_technical_filter(
    result: ScreeningResult, remaining: list[Stock]
) -> ScreeningResult:
    stale_symbols = [s.symbol for s in remaining if s.is_stale]
    status = "degraded" if stale_symbols or result.excluded_symbols else "ok"
    return ScreeningResult(
        status=status,
        results=remaining,
        stale_symbols=stale_symbols,
        excluded_symbols=result.excluded_symbols,
        as_of=result.as_of,
    )


class ScreeningService:
    """Orchestrates a screen: fetch the universe, filter, rank, and report
    degradation. Depends only on the StockDataProvider port (DIP) — it has
    no idea whether quotes came from yfinance, a cache, or a test double."""

    def __init__(
        self,
        provider: StockDataProvider,
        universe: list[str],
        technical_filter_stage: TechnicalFilterStage | None = None,
    ):
        self._provider = provider
        self._universe = universe
        self._technical_filter_stage = technical_filter_stage

    def screen(self, criteria: ScreeningCriteria) -> ScreeningResult:
        result = self.screen_with_matcher(FilterChain.from_criteria(criteria))
        if criteria.above_sma_window is None:
            return result
        if self._technical_filter_stage is None:
            raise ValueError("above_sma_window given but no TechnicalFilterStage is configured")
        remaining = self._technical_filter_stage.apply(result.results, criteria.above_sma_window)
        return _rerank_after_technical_filter(result, remaining)

    def screen_with_matcher(self, matcher: Matcher) -> ScreeningResult:
        """Same as `screen`, but takes any Matcher — the structured
        FilterChain built above, or a DslMatcher parsed from a query
        string. Lets saved screens and the query endpoint reuse this exact
        fetch/rank/degrade logic regardless of which mode built the match
        condition."""
        batch = self._provider.get_quotes(self._universe)

        filtered = [s for s in batch.stocks if matcher.matches(s)]
        ranked = sorted(filtered, key=_rank_key)

        stale_symbols = [s.symbol for s in filtered if s.is_stale]
        status = "degraded" if stale_symbols or batch.excluded_symbols else "ok"

        return ScreeningResult(
            status=status,
            results=ranked,
            stale_symbols=stale_symbols,
            excluded_symbols=batch.excluded_symbols,
            as_of=datetime.now(timezone.utc),
        )
