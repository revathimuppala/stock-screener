from datetime import datetime, timezone

from screener.domain.entities import ScreeningCriteria, Stock
from screener.domain.filters import FilterChain


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


class TestFilterChain:
    def test_empty_criteria_matches_everything(self):
        chain = FilterChain.from_criteria(ScreeningCriteria())
        assert chain.matches(make_stock()) is True

    def test_all_criteria_must_hold(self):
        criteria = ScreeningCriteria(pe_min=10, pe_max=20, sector="Technology")
        chain = FilterChain.from_criteria(criteria)

        assert chain.matches(make_stock(pe_ratio=15.0, sector="Technology")) is True
        assert chain.matches(make_stock(pe_ratio=15.0, sector="Energy")) is False
        assert chain.matches(make_stock(pe_ratio=99.0, sector="Technology")) is False

    def test_apply_filters_a_list_and_preserves_order(self):
        criteria = ScreeningCriteria(min_dividend_yield=0.01)
        chain = FilterChain.from_criteria(criteria)
        stocks = [
            make_stock(symbol="A", dividend_yield=0.02),
            make_stock(symbol="B", dividend_yield=0.001),
            make_stock(symbol="C", dividend_yield=0.05),
        ]

        result = chain.apply(stocks)

        assert [s.symbol for s in result] == ["A", "C"]
