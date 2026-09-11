from datetime import datetime, timezone

import pytest

from screener.domain.entities import Stock
from screener.domain.filters import (
    DebtToEquityMaxFilter,
    EarningsGrowthMinFilter,
    FiftyTwoWeekProximityFilter,
    PriceToBookMaxFilter,
    RevenueGrowthMinFilter,
    RoeMinFilter,
)


def make_stock(**overrides) -> Stock:
    defaults = dict(
        symbol="AAPL",
        name="Apple Inc.",
        sector="Technology",
        price=190.0,
        pe_ratio=15.0,
        market_cap=3_000_000_000_000.0,
        dividend_yield=0.005,
        as_of=datetime(2026, 1, 1, tzinfo=timezone.utc),
        is_stale=False,
    )
    defaults.update(overrides)
    return Stock(**defaults)


class TestRoeMinFilter:
    def test_meets_minimum(self):
        f = RoeMinFilter(roe_min=0.15)
        assert f.matches(make_stock(roe=0.20)) is True

    def test_below_minimum(self):
        f = RoeMinFilter(roe_min=0.15)
        assert f.matches(make_stock(roe=0.10)) is False

    def test_none_fails_a_positive_minimum(self):
        f = RoeMinFilter(roe_min=0.15)
        assert f.matches(make_stock(roe=None)) is False


class TestDebtToEquityMaxFilter:
    def test_within_max(self):
        f = DebtToEquityMaxFilter(debt_to_equity_max=100)
        assert f.matches(make_stock(debt_to_equity=78.4)) is True

    def test_above_max(self):
        f = DebtToEquityMaxFilter(debt_to_equity_max=50)
        assert f.matches(make_stock(debt_to_equity=78.4)) is False

    def test_none_fails_a_max_constraint(self):
        f = DebtToEquityMaxFilter(debt_to_equity_max=50)
        assert f.matches(make_stock(debt_to_equity=None)) is False


class TestPriceToBookMaxFilter:
    def test_within_max(self):
        f = PriceToBookMaxFilter(price_to_book_max=5)
        assert f.matches(make_stock(price_to_book=2.6)) is True

    def test_above_max(self):
        f = PriceToBookMaxFilter(price_to_book_max=5)
        assert f.matches(make_stock(price_to_book=44.3)) is False


class TestEarningsGrowthMinFilter:
    def test_meets_minimum(self):
        f = EarningsGrowthMinFilter(earnings_growth_min=0.10)
        assert f.matches(make_stock(earnings_growth=0.287)) is True

    def test_below_minimum(self):
        f = EarningsGrowthMinFilter(earnings_growth_min=0.30)
        assert f.matches(make_stock(earnings_growth=0.287)) is False


class TestRevenueGrowthMinFilter:
    def test_meets_minimum(self):
        f = RevenueGrowthMinFilter(revenue_growth_min=0.10)
        assert f.matches(make_stock(revenue_growth=0.164)) is True

    def test_below_minimum(self):
        f = RevenueGrowthMinFilter(revenue_growth_min=0.20)
        assert f.matches(make_stock(revenue_growth=0.164)) is False


class TestFiftyTwoWeekProximityFilter:
    def test_within_pct_of_high_matches(self):
        f = FiftyTwoWeekProximityFilter(within_pct=0.05)
        assert f.matches(make_stock(price=98.0, fifty_two_week_high=100.0)) is True

    def test_outside_pct_of_high_does_not_match(self):
        f = FiftyTwoWeekProximityFilter(within_pct=0.05)
        assert f.matches(make_stock(price=80.0, fifty_two_week_high=100.0)) is False

    def test_at_the_high_matches(self):
        f = FiftyTwoWeekProximityFilter(within_pct=0.05)
        assert f.matches(make_stock(price=100.0, fifty_two_week_high=100.0)) is True

    def test_none_high_does_not_match(self):
        f = FiftyTwoWeekProximityFilter(within_pct=0.05)
        assert f.matches(make_stock(price=100.0, fifty_two_week_high=None)) is False

    @pytest.mark.parametrize("within_pct", [0.0, 1.0])
    def test_boundary_pct_values(self, within_pct):
        f = FiftyTwoWeekProximityFilter(within_pct=within_pct)
        assert f.matches(make_stock(price=100.0, fifty_two_week_high=100.0)) is True
