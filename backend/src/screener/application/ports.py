from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from screener.domain.entities import FilingLink, PriceBar, RawFinancials, SavedScreen, Stock


@dataclass(frozen=True, slots=True)
class ProviderBatchResult:
    """Result of asking a provider for quotes on a batch of symbols.

    `stocks` holds every symbol that could be resolved (fresh or stale — see
    `Stock.is_stale`); `excluded_symbols` holds symbols that could not be
    resolved at all. Splitting the two lets the application layer stay
    ignorant of *why* a symbol is missing (retry exhaustion, breaker open,
    no cache) — that reasoning is entirely the provider's concern.
    """

    stocks: list[Stock]
    excluded_symbols: list[str]


class StockDataProvider(Protocol):
    """The only port the application layer depends on for market data.
    Concrete implementations live in the infrastructure layer (DIP)."""

    def get_quotes(self, symbols: list[str]) -> ProviderBatchResult: ...


class WatchlistRepository(Protocol):
    """Persistence port for a user's watchlist. Concrete implementations
    (SQLite, in-memory) live in the infrastructure/test layers (DIP)."""

    def add(self, symbol: str) -> None: ...
    def remove(self, symbol: str) -> None: ...
    def list_symbols(self) -> list[str]: ...


class SavedScreenRepository(Protocol):
    """Persistence port for saved screens. Concrete implementations
    (SQLite, in-memory) live in the infrastructure/test layers (DIP)."""

    def save(self, screen: SavedScreen) -> None: ...
    def list(self) -> list[SavedScreen]: ...
    def get(self, screen_id: str) -> SavedScreen | None: ...
    def delete(self, screen_id: str) -> None: ...


class PriceHistoryProvider(Protocol):
    """Port for historical daily closes, used by the moving-average filter
    stage and by backtesting. Concrete implementations (yfinance, a
    file-backed cache wrapping it) live in the infrastructure layer (DIP)."""

    def get_history(self, symbol: str, start: date, end: date) -> list[PriceBar]: ...


class FinancialsProvider(Protocol):
    """Port for balance-sheet/quarterly-statement/holders data — used by
    the debt_to_assets and cfo_to_operating_profit enrichment and by the
    company-detail endpoint. Concrete implementation lives in the
    infrastructure layer (DIP)."""

    def get_financials(self, symbol: str) -> RawFinancials: ...


class FilingLinkProvider(Protocol):
    """Port for SEC filing links — used by the company-detail endpoint.
    Concrete implementation (SecEdgarClient) lives in the infrastructure
    layer (DIP)."""

    def get_filing_links(self, symbol: str) -> list[FilingLink]: ...


class MarketConstituentsProvider(Protocol):
    """Port for a market/index's constituent symbol list (already in
    yfinance-compatible ticker form, e.g. ".NS"/".BO" suffixes, "-" share
    classes). Concrete implementations live in the infrastructure layer
    (DIP)."""

    def get_symbols(self, market_id: str) -> list[str]: ...
