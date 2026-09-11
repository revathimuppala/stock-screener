from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

from screener.application.ports import PriceHistoryProvider, StockDataProvider
from screener.domain.backtest.models import (
    BacktestMatch,
    BacktestPerformance,
    BacktestResult,
    BacktestSummary,
)
from screener.domain.entities import PriceBar
from screener.domain.matcher import Matcher

# Extra days fetched past `end` so a holding period that extends beyond the
# requested window can still find an exit price when the data exists.
_MAX_HOLDING_LOOKAHEAD_DAYS = 400


class BacktestService:
    """Replays a Matcher (structured criteria or a DSL query) over real
    historical daily prices. Fundamentals (P/E, ROE, ...) are frozen at
    today's values for the whole window — yfinance has no historical
    point-in-time fundamentals — every result says so via
    `fundamentals_as_of`. Deliberately separate from ScreeningService,
    which answers "what matches today", not "what matched on each day"."""

    def __init__(
        self,
        stock_provider: StockDataProvider,
        price_history_provider: PriceHistoryProvider,
        universe: list[str],
    ):
        self._stock_provider = stock_provider
        self._price_history_provider = price_history_provider
        self._universe = universe

    def run(self, matcher: Matcher, start: date, end: date, holding_period_days: int) -> BacktestResult:
        batch = self._stock_provider.get_quotes(self._universe)
        current_by_symbol = {s.symbol: s for s in batch.stocks}
        excluded_symbols = list(batch.excluded_symbols)
        warnings: list[str] = []

        timeline: list[BacktestMatch] = []
        performances: list[BacktestPerformance] = []

        history_end = end + timedelta(days=min(holding_period_days, _MAX_HOLDING_LOOKAHEAD_DAYS))

        for symbol in self._universe:
            current_stock = current_by_symbol.get(symbol)
            if current_stock is None:
                continue  # already recorded in excluded_symbols by the provider

            bars = self._price_history_provider.get_history(symbol, start, history_end)
            in_window = [b for b in bars if start <= b.date <= end]
            if not in_window:
                excluded_symbols.append(symbol)
                continue

            for bar in in_window:
                snapshot = replace(current_stock, price=bar.close, as_of=_as_datetime(bar.date))
                if not matcher.matches(snapshot):
                    continue
                match = BacktestMatch(symbol=symbol, match_date=bar.date, match_price=bar.close)
                timeline.append(match)
                performances.append(_evaluate_performance(match, bars, holding_period_days))

        timeline.sort(key=lambda m: (m.match_date, m.symbol))
        performances.sort(key=lambda p: (p.match.match_date, p.match.symbol))

        return BacktestResult(
            status="completed",
            timeline=timeline,
            performances=performances,
            summary=_summarize(performances),
            excluded_symbols=excluded_symbols,
            warnings=warnings,
            fundamentals_as_of=datetime.now(timezone.utc),
        )


def _as_datetime(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def _evaluate_performance(
    match: BacktestMatch, bars: list[PriceBar], holding_period_days: int
) -> BacktestPerformance:
    target_exit_date = match.match_date + timedelta(days=holding_period_days)
    exit_bar = next((b for b in bars if b.date >= target_exit_date), None)
    if exit_bar is None:
        return BacktestPerformance(
            match=match, exit_date=None, exit_price=None, return_pct=None, status="pending"
        )
    return_pct = (exit_bar.close / match.match_price - 1) * 100
    return BacktestPerformance(
        match=match,
        exit_date=exit_bar.date,
        exit_price=exit_bar.close,
        return_pct=return_pct,
        status="completed",
    )


def _summarize(performances: list[BacktestPerformance]) -> BacktestSummary:
    completed = [p for p in performances if p.status == "completed"]
    pending = [p for p in performances if p.status == "pending"]
    returns = [p.return_pct for p in completed if p.return_pct is not None]

    return BacktestSummary(
        total_matches=len(performances),
        completed_count=len(completed),
        pending_count=len(pending),
        avg_return_pct=(sum(returns) / len(returns)) if returns else None,
        win_rate=(sum(1 for r in returns if r > 0) / len(returns)) if returns else None,
        best_return_pct=max(returns) if returns else None,
        worst_return_pct=min(returns) if returns else None,
    )
