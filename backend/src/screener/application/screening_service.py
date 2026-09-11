from __future__ import annotations

from datetime import datetime, timezone

from screener.application.ports import StockDataProvider
from screener.domain.entities import ScreeningCriteria, ScreeningResult, Stock
from screener.domain.filters import FilterChain


def _rank_key(stock: Stock) -> tuple[float, float]:
    yield_desc = -(stock.dividend_yield or 0.0)
    pe_asc = stock.pe_ratio if stock.pe_ratio is not None else float("inf")
    return (yield_desc, pe_asc)


class ScreeningService:
    """Orchestrates a screen: fetch the universe, filter, rank, and report
    degradation. Depends only on the StockDataProvider port (DIP) — it has
    no idea whether quotes came from yfinance, a cache, or a test double."""

    def __init__(self, provider: StockDataProvider, universe: list[str]):
        self._provider = provider
        self._universe = universe

    def screen(self, criteria: ScreeningCriteria) -> ScreeningResult:
        batch = self._provider.get_quotes(self._universe)

        chain = FilterChain.from_criteria(criteria)
        filtered = chain.apply(batch.stocks)
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
