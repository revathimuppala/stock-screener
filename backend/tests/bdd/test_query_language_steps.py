from datetime import datetime, timezone

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from screener.application.ports import ProviderBatchResult
from screener.application.screening_service import ScreeningService
from screener.domain.dsl.errors import DslError
from screener.domain.dsl.matcher import DslMatcher
from screener.domain.entities import Stock

scenarios("query_language.feature")

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_stock(symbol: str, **overrides) -> Stock:
    defaults = dict(
        symbol=symbol,
        name=f"{symbol} Inc.",
        sector="Technology",
        price=100.0,
        pe_ratio=15.0,
        market_cap=1e9,
        dividend_yield=0.0,
        as_of=AS_OF,
        is_stale=False,
        roe=0.1,
    )
    defaults.update(overrides)
    return Stock(**defaults)


class FakeProvider:
    def __init__(self, stocks):
        self._stocks = stocks

    def get_quotes(self, symbols):
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=[])


@pytest.fixture
def context() -> dict:
    return {}


@given("a universe of stocks with known fundamentals")
def known_universe(context: dict) -> None:
    context["stocks"] = [
        make_stock("CHEAP_TECH", sector="Technology", pe_ratio=12.0, roe=0.02),
        make_stock("PRICEY_TECH", sector="Technology", pe_ratio=35.0, roe=0.20),
        make_stock("ENERGY_CO", sector="Energy", pe_ratio=15.0, roe=0.30),
    ]


@when(parsers.parse("I screen with the query: {query}"))
def screen_with_query(context: dict, query: str) -> None:
    try:
        matcher = DslMatcher(query)
    except DslError as exc:
        context["error"] = exc
        return
    service = ScreeningService(
        provider=FakeProvider(context["stocks"]), universe=[s.symbol for s in context["stocks"]]
    )
    context["result"] = service.screen_with_matcher(matcher)


@then(parsers.parse("every result has a P/E ratio below {pe_max:g}"))
def assert_pe_below(context: dict, pe_max: float) -> None:
    assert context["result"].results
    assert all(s.pe_ratio < pe_max for s in context["result"].results)


@then(parsers.parse('every result is in sector "{sector}"'))
def assert_sector(context: dict, sector: str) -> None:
    assert context["result"].results
    assert all(s.sector == sector for s in context["result"].results)


@then("the query is rejected with a parse error")
def assert_rejected(context: dict) -> None:
    assert "error" in context
    assert isinstance(context["error"], DslError)
