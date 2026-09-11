from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from screener.application.financials_enrichment_stage import FinancialsEnrichmentStage
from screener.application.ports import StockDataProvider
from screener.application.technical_filter_stage import TechnicalFilterStage
from screener.domain.entities import ScreeningCriteria, ScreeningResult, Stock
from screener.domain.filters import FilterChain
from screener.domain.matcher import Matcher


def _rank_key(stock: Stock) -> tuple[float, float]:
    yield_desc = -(stock.dividend_yield or 0.0)
    pe_asc = stock.pe_ratio if stock.pe_ratio is not None else float("inf")
    return (yield_desc, pe_asc)


def _with_results(result: ScreeningResult, results: list[Stock]) -> ScreeningResult:
    """Recomputes stale_symbols/status from a (possibly narrowed or
    enriched) results list, preserving everything else about the batch."""
    stale_symbols = [s.symbol for s in results if s.is_stale]
    status = "degraded" if stale_symbols or result.excluded_symbols else "ok"
    return replace(result, results=results, stale_symbols=stale_symbols, status=status)


class ScreeningService:
    """Orchestrates a screen: fetch the universe, filter, rank, enrich, and
    report degradation. Depends only on the StockDataProvider port (DIP) —
    it has no idea whether quotes came from yfinance, a cache, or a test
    double."""

    def __init__(
        self,
        provider: StockDataProvider,
        universe: list[str],
        technical_filter_stage: TechnicalFilterStage | None = None,
        financials_enrichment_stage: FinancialsEnrichmentStage | None = None,
    ):
        self._provider = provider
        self._universe = universe
        self._technical_filter_stage = technical_filter_stage
        self._financials_enrichment_stage = financials_enrichment_stage

    def screen(self, criteria: ScreeningCriteria) -> ScreeningResult:
        result = self.screen_with_matcher(
            FilterChain.from_criteria(criteria), universe_override=criteria.symbols
        )

        if criteria.above_sma_window is not None:
            if self._technical_filter_stage is None:
                raise ValueError("above_sma_window given but no TechnicalFilterStage is configured")
            result = _with_results(
                result, self._technical_filter_stage.apply(result.results, criteria.above_sma_window)
            )

        if criteria.rsi_min is not None or criteria.rsi_max is not None:
            if self._technical_filter_stage is None:
                raise ValueError("rsi_min/rsi_max given but no TechnicalFilterStage is configured")
            result = _with_results(
                result,
                self._technical_filter_stage.filter_by_rsi(result.results, criteria.rsi_min, criteria.rsi_max),
            )

        return result

    def screen_with_matcher(self, matcher: Matcher, universe_override: list[str] | None = None) -> ScreeningResult:
        """Same as `screen`, but takes any Matcher — the structured
        FilterChain built above, or a DslMatcher parsed from a query
        string. Lets saved screens and the query endpoint reuse this exact
        fetch/rank/enrich/degrade logic regardless of which mode built the
        match condition — enrichment (technical + financials display
        columns) always runs here when a stage is configured, so a DSL
        query or a saved screen never shows blank columns a structured
        screen would have filled in. `universe_override` screens an
        explicit symbol list instead of the default universe."""
        universe = universe_override if universe_override else self._universe
        batch = self._provider.get_quotes(universe)

        filtered = [s for s in batch.stocks if matcher.matches(s)]
        ranked = sorted(filtered, key=_rank_key)

        stale_symbols = [s.symbol for s in filtered if s.is_stale]
        status = "degraded" if stale_symbols or batch.excluded_symbols else "ok"

        result = ScreeningResult(
            status=status,
            results=ranked,
            stale_symbols=stale_symbols,
            excluded_symbols=batch.excluded_symbols,
            as_of=datetime.now(timezone.utc),
        )

        if self._technical_filter_stage is not None:
            result = _with_results(result, self._technical_filter_stage.enrich(result.results))
        if self._financials_enrichment_stage is not None:
            result = _with_results(result, self._financials_enrichment_stage.enrich(result.results))

        return result
