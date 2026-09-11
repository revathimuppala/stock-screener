from datetime import datetime, timezone

from screener.domain.entities import Stock
from screener.infrastructure.resilient_provider import ResilientStockDataProvider

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


class ConcurrentFetcher:
    """Every symbol always succeeds — used to prove concurrent resolves
    across many distinct keys don't corrupt ResilientFetcher's shared
    TTLCache or drop/duplicate results, now that get_quotes uses a thread
    pool instead of a sequential loop."""

    def __init__(self):
        self.calls: list[str] = []

    def fetch(self, symbol: str) -> Stock:
        self.calls.append(symbol)
        return Stock(
            symbol=symbol,
            name=f"{symbol} Inc.",
            sector="Technology",
            price=100.0,
            pe_ratio=15.0,
            market_cap=1e9,
            dividend_yield=0.01,
            as_of=AS_OF,
            is_stale=False,
        )


class TestConcurrentGetQuotes:
    def test_many_symbols_all_resolve_with_no_corruption_or_loss(self):
        symbols = [f"SYM{i}" for i in range(200)]
        fetcher = ConcurrentFetcher()
        provider = ResilientStockDataProvider(fetcher=fetcher, max_workers=20)

        result = provider.get_quotes(symbols)

        assert result.excluded_symbols == []
        assert [s.symbol for s in result.stocks] == symbols  # preserves input order
        assert len(fetcher.calls) == 200

    def test_repeated_concurrent_calls_keep_a_consistent_cache(self):
        symbols = [f"SYM{i}" for i in range(50)]
        fetcher = ConcurrentFetcher()
        provider = ResilientStockDataProvider(fetcher=fetcher, max_workers=10)

        first = provider.get_quotes(symbols)
        second = provider.get_quotes(symbols)

        assert [s.symbol for s in first.stocks] == symbols
        assert [s.symbol for s in second.stocks] == symbols
