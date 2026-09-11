from screener.application.watchlist_service import WatchlistService


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


class TestWatchlistService:
    def test_add_symbol_appears_in_list(self):
        service = WatchlistService(repository=InMemoryWatchlistRepository())

        service.add_symbol("aapl")

        assert service.list_symbols() == ["AAPL"]

    def test_remove_symbol(self):
        repo = InMemoryWatchlistRepository()
        service = WatchlistService(repository=repo)
        service.add_symbol("AAPL")

        service.remove_symbol("AAPL")

        assert service.list_symbols() == []

    def test_adding_the_same_symbol_twice_is_idempotent(self):
        service = WatchlistService(repository=InMemoryWatchlistRepository())

        service.add_symbol("AAPL")
        service.add_symbol("AAPL")

        assert service.list_symbols() == ["AAPL"]

    def test_symbols_are_normalized_to_uppercase(self):
        service = WatchlistService(repository=InMemoryWatchlistRepository())

        service.add_symbol("aapl")
        service.add_symbol("AAPL")

        assert service.list_symbols() == ["AAPL"]
