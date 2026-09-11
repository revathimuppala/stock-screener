from dataclasses import replace
from datetime import datetime, timezone

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from screener.application.ports import ProviderBatchResult
from screener.application.screening_service import ScreeningService
from screener.domain.entities import ScreeningCriteria, Stock

scenarios("screening.feature")

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
    )
    defaults.update(overrides)
    return Stock(**defaults)


class FakeProvider:
    def __init__(self, stocks: list[Stock], excluded_symbols: list[str]):
        self._stocks = stocks
        self._excluded_symbols = excluded_symbols

    def get_quotes(self, symbols: list[str]) -> ProviderBatchResult:
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=self._excluded_symbols)


@pytest.fixture
def context() -> dict:
    return {"excluded": []}


def _run_screen(context: dict, criteria: ScreeningCriteria) -> None:
    provider = FakeProvider(context["stocks"], context["excluded"])
    service = ScreeningService(provider=provider, universe=context["universe_symbols"])
    context["result"] = service.screen(criteria)


@given("a universe of stocks with known fundamentals")
def known_universe(context: dict) -> None:
    context["stocks"] = [
        make_stock("CHEAP_TECH", sector="Technology", pe_ratio=12.0, dividend_yield=0.02),
        make_stock("PRICEY_TECH", sector="Technology", pe_ratio=35.0, dividend_yield=0.0),
        make_stock("ENERGY_CO", sector="Energy", pe_ratio=15.0, dividend_yield=0.03),
    ]
    context["universe_symbols"] = [s.symbol for s in context["stocks"]]


@given("the data provider is currently down")
def provider_down(context: dict) -> None:
    context["provider_down"] = True


@given("the cache holds fresh-enough data for every symbol")
def cache_holds_fresh_data(context: dict) -> None:
    context["stocks"] = [replace(s, is_stale=True) for s in context["stocks"]]


@given("one symbol has no data available from the provider or the cache")
def one_symbol_unavailable(context: dict) -> None:
    unavailable = context["stocks"].pop()
    context["excluded"] = [unavailable.symbol]


@when(parsers.parse("I screen with a P/E range of {pe_min:g} to {pe_max:g}"))
def screen_pe_range(context: dict, pe_min: float, pe_max: float) -> None:
    _run_screen(context, ScreeningCriteria(pe_min=pe_min, pe_max=pe_max))


@when(parsers.parse('I screen for sector "{sector}" with minimum dividend yield {min_yield:g}'))
def screen_sector_and_yield(context: dict, sector: str, min_yield: float) -> None:
    _run_screen(context, ScreeningCriteria(sector=sector, min_dividend_yield=min_yield))


@when("I screen with no criteria")
def screen_no_criteria(context: dict) -> None:
    _run_screen(context, ScreeningCriteria())


@then(parsers.parse("every result has a P/E ratio between {pe_min:g} and {pe_max:g}"))
def assert_pe_between(context: dict, pe_min: float, pe_max: float) -> None:
    assert all(pe_min <= s.pe_ratio <= pe_max for s in context["result"].results)


@then(parsers.parse('every result is in sector "{sector}"'))
def assert_sector(context: dict, sector: str) -> None:
    assert all(s.sector == sector for s in context["result"].results)


@then(parsers.parse("every result has a dividend yield of at least {min_yield:g}"))
def assert_min_yield(context: dict, min_yield: float) -> None:
    assert all(s.dividend_yield >= min_yield for s in context["result"].results)


@then(parsers.parse('the response status is "{status}"'))
def assert_status(context: dict, status: str) -> None:
    assert context["result"].status == status


@then("the results list is empty")
def assert_results_empty(context: dict) -> None:
    assert context["result"].results == []


@then("every result is marked stale")
def assert_all_stale(context: dict) -> None:
    assert context["result"].results
    assert all(s.is_stale for s in context["result"].results)


@then("that symbol is listed in excluded symbols")
def assert_symbol_excluded(context: dict) -> None:
    assert context["excluded"][0] in context["result"].excluded_symbols


@then("results are still returned for the remaining symbols")
def assert_remaining_results(context: dict) -> None:
    assert len(context["result"].results) > 0
