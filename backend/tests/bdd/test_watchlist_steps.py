import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from screener.application.watchlist_service import WatchlistService

scenarios("watchlist.feature")


class InMemoryWatchlistRepository:
    def __init__(self):
        self._symbols: list[str] = []

    def add(self, symbol: str) -> None:
        if symbol not in self._symbols:
            self._symbols.append(symbol)

    def remove(self, symbol: str) -> None:
        if symbol in self._symbols:
            self._symbols.remove(symbol)

    def list_symbols(self) -> list[str]:
        return list(self._symbols)


@pytest.fixture
def context() -> dict:
    return {"service": WatchlistService(repository=InMemoryWatchlistRepository())}


@given("an empty watchlist")
def empty_watchlist(context: dict) -> None:
    assert context["service"].list_symbols() == []


@given(parsers.parse('a watchlist containing "{symbol}"'))
def watchlist_containing(context: dict, symbol: str) -> None:
    context["service"].add_symbol(symbol)


@when(parsers.parse('I add symbol "{symbol}" to the watchlist'))
def add_symbol(context: dict, symbol: str) -> None:
    context["service"].add_symbol(symbol)


@when(parsers.parse('I remove symbol "{symbol}" from the watchlist'))
def remove_symbol(context: dict, symbol: str) -> None:
    context["service"].remove_symbol(symbol)


@then(parsers.parse('the watchlist contains "{symbol}"'))
def assert_contains(context: dict, symbol: str) -> None:
    assert symbol in context["service"].list_symbols()


@then(parsers.parse('the watchlist does not contain "{symbol}"'))
def assert_not_contains(context: dict, symbol: str) -> None:
    assert symbol not in context["service"].list_symbols()


@then(parsers.parse('the watchlist contains "{symbol}" exactly once'))
def assert_contains_once(context: dict, symbol: str) -> None:
    assert context["service"].list_symbols().count(symbol) == 1
