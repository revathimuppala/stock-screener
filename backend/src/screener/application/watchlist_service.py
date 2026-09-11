from __future__ import annotations

from screener.application.ports import WatchlistRepository


class WatchlistService:
    """Use case: manage a user's watchlist. Depends only on the
    WatchlistRepository port (DIP) — persistence technology is invisible
    here."""

    def __init__(self, repository: WatchlistRepository):
        self._repository = repository

    def add_symbol(self, symbol: str) -> None:
        self._repository.add(symbol.upper())

    def remove_symbol(self, symbol: str) -> None:
        self._repository.remove(symbol.upper())

    def list_symbols(self) -> list[str]:
        return self._repository.list_symbols()
