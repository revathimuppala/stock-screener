from datetime import datetime, timezone

import pytest

from screener.domain.dsl.ast import And, Comparison, Not, Or
from screener.domain.dsl.errors import DslError
from screener.domain.dsl.matcher import DslMatcher
from screener.domain.entities import Stock

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_stock(**overrides) -> Stock:
    defaults = dict(
        symbol="AAPL",
        name="Apple Inc.",
        sector="Technology",
        price=190.0,
        pe_ratio=15.0,
        market_cap=3e12,
        dividend_yield=0.005,
        as_of=AS_OF,
        is_stale=False,
        roe=0.2,
    )
    defaults.update(overrides)
    return Stock(**defaults)


class TestDslMatcherOperators:
    @pytest.mark.parametrize(
        "op,threshold,expected",
        [
            ("<", 20.0, True),
            ("<", 10.0, False),
            ("<=", 15.0, True),
            (">", 10.0, True),
            (">", 20.0, False),
            (">=", 15.0, True),
            ("=", 15.0, True),
            ("!=", 20.0, True),
        ],
    )
    def test_numeric_operators(self, op, threshold, expected):
        matcher = DslMatcher(f"pe {op} {threshold}")
        assert matcher.matches(make_stock(pe_ratio=15.0)) is expected

    def test_string_equality_is_case_insensitive(self):
        matcher = DslMatcher('sector = "technology"')
        assert matcher.matches(make_stock(sector="Technology")) is True

    def test_string_inequality(self):
        matcher = DslMatcher('sector != "Energy"')
        assert matcher.matches(make_stock(sector="Technology")) is True


class TestDslMatcherBooleanLogic:
    def test_and(self):
        matcher = DslMatcher("pe < 20 AND roe > 0.1")
        assert matcher.matches(make_stock(pe_ratio=15.0, roe=0.2)) is True
        assert matcher.matches(make_stock(pe_ratio=25.0, roe=0.2)) is False

    def test_or(self):
        matcher = DslMatcher("pe < 5 OR roe > 0.1")
        assert matcher.matches(make_stock(pe_ratio=15.0, roe=0.2)) is True
        assert matcher.matches(make_stock(pe_ratio=15.0, roe=0.05)) is False

    def test_not(self):
        matcher = DslMatcher("NOT pe < 10")
        assert matcher.matches(make_stock(pe_ratio=15.0)) is True
        assert matcher.matches(make_stock(pe_ratio=5.0)) is False

    def test_nested_grouping(self):
        matcher = DslMatcher('(roe > 0.5 OR pe < 20) AND sector = "Technology"')
        assert matcher.matches(make_stock(pe_ratio=15.0, roe=0.01, sector="Technology")) is True
        assert matcher.matches(make_stock(pe_ratio=15.0, roe=0.01, sector="Energy")) is False


class TestDslMatcherNoneHandling:
    def test_none_field_value_never_matches_any_operator(self):
        for op in ("<", "<=", ">", ">=", "=", "!="):
            matcher = DslMatcher(f"roe {op} 0.1")
            assert matcher.matches(make_stock(roe=None)) is False

    def test_none_field_value_does_not_raise(self):
        matcher = DslMatcher("roe != 0.1")
        # should not raise even though None != 0.1 would normally be True
        assert matcher.matches(make_stock(roe=None)) is False


class TestDslMatcherConstructionErrors:
    def test_invalid_query_raises_at_construction(self):
        with pytest.raises(DslError):
            DslMatcher("not_a_field < 20")
