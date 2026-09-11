from datetime import date, datetime, timezone

import pytest
from pytest_bdd import given, scenarios, then, when

from screener.application.backtest_service import BacktestService
from screener.application.ports import ProviderBatchResult
from screener.domain.entities import PriceBar, ScreeningCriteria, Stock
from screener.domain.filters import FilterChain

scenarios("backtesting.feature")

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_stock(**overrides) -> Stock:
    defaults = dict(
        symbol="AAPL",
        name="Apple Inc.",
        sector="Technology",
        price=100.0,
        pe_ratio=15.0,
        market_cap=1e9,
        dividend_yield=0.01,
        as_of=AS_OF,
        is_stale=False,
    )
    defaults.update(overrides)
    return Stock(**defaults)


class FakeStockProvider:
    def __init__(self, stocks, excluded=None):
        self._stocks = stocks
        self._excluded = excluded or []

    def get_quotes(self, symbols):
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=self._excluded)


class FakePriceHistoryProvider:
    def __init__(self, bars_by_symbol):
        self._bars_by_symbol = bars_by_symbol

    def get_history(self, symbol, start, end):
        return [b for b in self._bars_by_symbol.get(symbol, []) if start <= b.date <= end]


class _PriceBelowMatcher:
    def __init__(self, threshold):
        self._threshold = threshold

    def matches(self, stock):
        return stock.price < self._threshold


@pytest.fixture
def context() -> dict:
    return {}


@given("a symbol with 5 days of historical prices around a threshold")
def five_days_around_threshold(context: dict) -> None:
    context["stock"] = make_stock(symbol="AAPL")
    context["bars"] = {
        "AAPL": [
            PriceBar(date=date(2026, 1, 1), close=90.0),
            PriceBar(date=date(2026, 1, 2), close=110.0),
            PriceBar(date=date(2026, 1, 3), close=95.0),
            PriceBar(date=date(2026, 1, 4), close=120.0),
            PriceBar(date=date(2026, 1, 5), close=85.0),
        ]
    }
    context["window"] = (date(2026, 1, 1), date(2026, 1, 5))


@when('I backtest a "price below threshold" screen over that window')
def backtest_price_below(context: dict) -> None:
    service = BacktestService(
        stock_provider=FakeStockProvider([context["stock"]]),
        price_history_provider=FakePriceHistoryProvider(context["bars"]),
        universe=["AAPL"],
    )
    start, end = context["window"]
    context["result"] = service.run(
        matcher=_PriceBelowMatcher(100.0), start=start, end=end, holding_period_days=1
    )


@then("the timeline contains a match for each day price was below the threshold")
def assert_timeline_matches(context: dict) -> None:
    matched_dates = {m.match_date for m in context["result"].timeline}
    assert matched_dates == {date(2026, 1, 1), date(2026, 1, 3), date(2026, 1, 5)}


@given("a symbol with a P/E ratio of 15 today and price history that varies")
def symbol_with_frozen_pe(context: dict) -> None:
    context["stock"] = make_stock(symbol="AAPL", pe_ratio=15.0)
    context["bars"] = {
        "AAPL": [
            PriceBar(date=date(2026, 1, 1), close=90.0),
            PriceBar(date=date(2026, 1, 2), close=200.0),
            PriceBar(date=date(2026, 1, 3), close=50.0),
        ]
    }
    context["window"] = (date(2026, 1, 1), date(2026, 1, 3))


@when("I backtest a screen requiring P/E at or below 20")
def backtest_pe_at_or_below_20(context: dict) -> None:
    service = BacktestService(
        stock_provider=FakeStockProvider([context["stock"]]),
        price_history_provider=FakePriceHistoryProvider(context["bars"]),
        universe=["AAPL"],
    )
    start, end = context["window"]
    matcher = FilterChain.from_criteria(ScreeningCriteria(pe_max=20))
    context["result"] = service.run(matcher=matcher, start=start, end=end, holding_period_days=1)


@then("every day in the window matches, since P/E never changes during the backtest")
def assert_every_day_matches(context: dict) -> None:
    assert len(context["result"].timeline) == 3


@given("a symbol whose price history starts after the backtest window")
def symbol_starts_after_window(context: dict) -> None:
    context["stock"] = make_stock(symbol="LATE")
    context["bars"] = {"LATE": [PriceBar(date=date(2026, 6, 1), close=50.0)]}
    context["window"] = (date(2026, 1, 1), date(2026, 1, 5))


@when("I backtest a screen that would otherwise match")
def backtest_that_would_match(context: dict) -> None:
    service = BacktestService(
        stock_provider=FakeStockProvider([context["stock"]]),
        price_history_provider=FakePriceHistoryProvider(context["bars"]),
        universe=["LATE"],
    )
    start, end = context["window"]
    context["result"] = service.run(
        matcher=_PriceBelowMatcher(1000.0), start=start, end=end, holding_period_days=1
    )


@then("that symbol is listed in excluded symbols")
def assert_excluded(context: dict) -> None:
    assert "LATE" in context["result"].excluded_symbols
