from datetime import date, datetime, timezone

import pytest

from screener.application.backtest_service import BacktestService
from screener.application.ports import ProviderBatchResult
from screener.domain.entities import PriceBar, Stock
from screener.domain.filters import FilterChain
from screener.domain.entities import ScreeningCriteria

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


class FakeStockDataProvider:
    def __init__(self, stocks, excluded=None):
        self._stocks = stocks
        self._excluded = excluded or []

    def get_quotes(self, symbols):
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=self._excluded)


class FakePriceHistoryProvider:
    def __init__(self, bars_by_symbol: dict[str, list[PriceBar]]):
        self._bars_by_symbol = bars_by_symbol

    def get_history(self, symbol, start, end):
        return [b for b in self._bars_by_symbol.get(symbol, []) if start <= b.date <= end]


def bars(*pairs: tuple[str, float]) -> list[PriceBar]:
    return [PriceBar(date=date.fromisoformat(d), close=c) for d, c in pairs]


class TestBacktestServiceMatching:
    def test_records_a_match_for_every_day_price_satisfies_the_matcher(self):
        stock_provider = FakeStockDataProvider([make_stock(symbol="AAPL", pe_ratio=15.0)])
        price_history = FakePriceHistoryProvider(
            {
                "AAPL": bars(
                    ("2026-01-01", 90.0),  # below 100 -> matches "price < 100"
                    ("2026-01-02", 110.0),  # above -> no match
                    ("2026-01-03", 95.0),  # matches
                )
            }
        )
        service = BacktestService(
            stock_provider=stock_provider, price_history_provider=price_history, universe=["AAPL"]
        )
        matcher = _PriceBelowMatcher(100.0)

        result = service.run(
            matcher=matcher,
            start=date(2026, 1, 1),
            end=date(2026, 1, 3),
            holding_period_days=1,
        )

        assert [m.match_date.isoformat() for m in result.timeline] == ["2026-01-01", "2026-01-03"]
        assert result.status == "completed"

    def test_fundamentals_are_frozen_at_current_values_not_historical(self):
        # matcher checks pe_ratio (a fundamental), which never changes across
        # the backtest window even though price does
        stock_provider = FakeStockDataProvider([make_stock(symbol="AAPL", pe_ratio=15.0)])
        price_history = FakePriceHistoryProvider(
            {"AAPL": bars(("2026-01-01", 90.0), ("2026-01-02", 110.0))}
        )
        service = BacktestService(
            stock_provider=stock_provider, price_history_provider=price_history, universe=["AAPL"]
        )
        matcher = FilterChain.from_criteria(ScreeningCriteria(pe_max=20))

        result = service.run(
            matcher=matcher, start=date(2026, 1, 1), end=date(2026, 1, 2), holding_period_days=1
        )

        # both days match since pe_ratio=15 is frozen and always <= 20
        assert len(result.timeline) == 2
        assert result.fundamentals_as_of is not None


class TestBacktestServicePerformance:
    def test_completed_performance_when_holding_period_is_covered(self):
        stock_provider = FakeStockDataProvider([make_stock(symbol="AAPL")])
        price_history = FakePriceHistoryProvider(
            {"AAPL": bars(("2026-01-01", 100.0), ("2026-01-02", 105.0), ("2026-01-06", 110.0))}
        )
        service = BacktestService(
            stock_provider=stock_provider, price_history_provider=price_history, universe=["AAPL"]
        )
        matcher = _AlwaysMatcher()

        result = service.run(
            matcher=matcher, start=date(2026, 1, 1), end=date(2026, 1, 1), holding_period_days=5
        )

        assert len(result.performances) == 1
        perf = result.performances[0]
        assert perf.status == "completed"
        assert perf.exit_price == 110.0
        assert perf.return_pct == pytest.approx(10.0)

    def test_pending_performance_when_holding_period_runs_past_available_data(self):
        stock_provider = FakeStockDataProvider([make_stock(symbol="AAPL")])
        price_history = FakePriceHistoryProvider({"AAPL": bars(("2026-01-01", 100.0))})
        service = BacktestService(
            stock_provider=stock_provider, price_history_provider=price_history, universe=["AAPL"]
        )
        matcher = _AlwaysMatcher()

        result = service.run(
            matcher=matcher, start=date(2026, 1, 1), end=date(2026, 1, 1), holding_period_days=30
        )

        assert result.performances[0].status == "pending"
        assert result.performances[0].return_pct is None
        assert result.summary.pending_count == 1
        assert result.summary.completed_count == 0


class TestBacktestServiceExclusions:
    def test_symbol_with_no_price_history_in_range_is_excluded(self):
        stock_provider = FakeStockDataProvider([make_stock(symbol="LATE_IPO")])
        price_history = FakePriceHistoryProvider(
            {"LATE_IPO": bars(("2026-06-01", 50.0))}  # nothing in the requested window
        )
        service = BacktestService(
            stock_provider=stock_provider, price_history_provider=price_history, universe=["LATE_IPO"]
        )

        result = service.run(
            matcher=_AlwaysMatcher(), start=date(2026, 1, 1), end=date(2026, 1, 5), holding_period_days=1
        )

        assert "LATE_IPO" in result.excluded_symbols
        assert result.timeline == []

    def test_symbol_excluded_by_the_stock_provider_is_also_excluded_from_the_backtest(self):
        stock_provider = FakeStockDataProvider([], excluded=["BAD"])
        price_history = FakePriceHistoryProvider({})
        service = BacktestService(
            stock_provider=stock_provider, price_history_provider=price_history, universe=["BAD"]
        )

        result = service.run(
            matcher=_AlwaysMatcher(), start=date(2026, 1, 1), end=date(2026, 1, 5), holding_period_days=1
        )

        assert "BAD" in result.excluded_symbols


class _AlwaysMatcher:
    def matches(self, stock) -> bool:
        return True


class _PriceBelowMatcher:
    def __init__(self, threshold: float):
        self._threshold = threshold

    def matches(self, stock) -> bool:
        return stock.price < self._threshold
