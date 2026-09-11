from datetime import datetime, timezone

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from screener.application.ports import ProviderBatchResult
from screener.application.saved_screen_service import SavedScreenService
from screener.application.screening_service import ScreeningService
from screener.domain.entities import ScreeningCriteria, Stock

scenarios("saved_screens.feature")

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


class InMemorySavedScreenRepository:
    def __init__(self):
        self._screens = {}

    def save(self, screen):
        self._screens[screen.id] = screen

    def list(self):
        return list(self._screens.values())

    def get(self, screen_id):
        return self._screens.get(screen_id)

    def delete(self, screen_id):
        self._screens.pop(screen_id, None)


class FakeProvider:
    def __init__(self, stocks):
        self._stocks = stocks

    def get_quotes(self, symbols):
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=[])


@pytest.fixture
def context() -> dict:
    return {"service": SavedScreenService(repository=InMemorySavedScreenRepository())}


@given("no saved screens")
def no_saved_screens(context: dict) -> None:
    assert context["service"].list() == []


@given(parsers.parse('I save a screen named "{name}" with a P/E max of {pe_max:g}'))
@when(parsers.parse('I save a screen named "{name}" with a P/E max of {pe_max:g}'))
def save_screen(context: dict, name: str, pe_max: float) -> None:
    context["saved"] = context["service"].save(name=name, criteria=ScreeningCriteria(pe_max=pe_max))


@given(parsers.parse('a saved screen named "{name}" with a P/E max of {pe_max:g}'))
def given_saved_screen(context: dict, name: str, pe_max: float) -> None:
    context["saved"] = context["service"].save(name=name, criteria=ScreeningCriteria(pe_max=pe_max))


@given("a universe of stocks with known fundamentals")
def known_universe(context: dict) -> None:
    context["stocks"] = [
        make_stock("CHEAP", pe_ratio=12.0),
        make_stock("EXPENSIVE", pe_ratio=40.0),
    ]


@when(parsers.parse('I run the saved screen "{name}"'))
def run_screen(context: dict, name: str) -> None:
    screening_service = ScreeningService(
        provider=FakeProvider(context["stocks"]), universe=[s.symbol for s in context["stocks"]]
    )
    result = screening_service.screen(context["saved"].criteria)
    context["result"] = result


@when(parsers.parse('I delete the saved screen "{name}"'))
def delete_screen(context: dict, name: str) -> None:
    context["service"].delete(context["saved"].id)


@then(parsers.parse('the saved screens list contains "{name}"'))
def assert_contains(context: dict, name: str) -> None:
    assert any(s.name == name for s in context["service"].list())


@then(parsers.parse('the saved screens list does not contain "{name}"'))
def assert_not_contains(context: dict, name: str) -> None:
    assert not any(s.name == name for s in context["service"].list())


@then(parsers.parse("every result has a P/E ratio at or below {pe_max:g}"))
def assert_pe_at_or_below(context: dict, pe_max: float) -> None:
    assert context["result"].results
    assert all(s.pe_ratio <= pe_max for s in context["result"].results)
