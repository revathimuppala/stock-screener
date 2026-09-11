from datetime import datetime, timezone

import pytest

from screener.domain.entities import Stock
from screener.domain.filters import (
    DividendYieldFilter,
    MarketCapFilter,
    PeRangeFilter,
    SectorFilter,
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


class TestPeRangeFilter:
    def test_stock_inside_range_matches(self):
        f = PeRangeFilter(pe_min=10, pe_max=20)
        assert f.matches(make_stock(pe_ratio=15.0)) is True

    def test_stock_below_range_does_not_match(self):
        f = PeRangeFilter(pe_min=10, pe_max=20)
        assert f.matches(make_stock(pe_ratio=9.99)) is False

    def test_stock_above_range_does_not_match(self):
        f = PeRangeFilter(pe_min=10, pe_max=20)
        assert f.matches(make_stock(pe_ratio=20.01)) is False

    @pytest.mark.parametrize("pe_ratio", [10.0, 20.0])
    def test_boundary_values_are_inclusive(self, pe_ratio):
        f = PeRangeFilter(pe_min=10, pe_max=20)
        assert f.matches(make_stock(pe_ratio=pe_ratio)) is True

    def test_none_pe_ratio_does_not_match_a_bounded_range(self):
        f = PeRangeFilter(pe_min=10, pe_max=20)
        assert f.matches(make_stock(pe_ratio=None)) is False

    def test_open_range_matches_anything(self):
        f = PeRangeFilter(pe_min=None, pe_max=None)
        assert f.matches(make_stock(pe_ratio=500.0)) is True


class TestMarketCapFilter:
    def test_within_range_matches(self):
        f = MarketCapFilter(market_cap_min=1e9, market_cap_max=None)
        assert f.matches(make_stock(market_cap=2e9)) is True

    def test_below_min_does_not_match(self):
        f = MarketCapFilter(market_cap_min=1e9, market_cap_max=None)
        assert f.matches(make_stock(market_cap=5e8)) is False

    def test_above_max_does_not_match(self):
        f = MarketCapFilter(market_cap_min=None, market_cap_max=1e9)
        assert f.matches(make_stock(market_cap=2e9)) is False


class TestSectorFilter:
    def test_matching_sector(self):
        f = SectorFilter(sector="Technology")
        assert f.matches(make_stock(sector="Technology")) is True

    def test_non_matching_sector(self):
        f = SectorFilter(sector="Energy")
        assert f.matches(make_stock(sector="Technology")) is False

    def test_case_insensitive_match(self):
        f = SectorFilter(sector="technology")
        assert f.matches(make_stock(sector="Technology")) is True


class TestDividendYieldFilter:
    def test_meets_minimum(self):
        f = DividendYieldFilter(min_dividend_yield=0.01)
        assert f.matches(make_stock(dividend_yield=0.02)) is True

    def test_below_minimum(self):
        f = DividendYieldFilter(min_dividend_yield=0.01)
        assert f.matches(make_stock(dividend_yield=0.005)) is False

    def test_none_yield_fails_a_positive_minimum(self):
        f = DividendYieldFilter(min_dividend_yield=0.01)
        assert f.matches(make_stock(dividend_yield=None)) is False
