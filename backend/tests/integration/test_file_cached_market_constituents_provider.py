from datetime import datetime, timedelta, timezone

import pytest

from screener.infrastructure.file_cached_market_constituents_provider import (
    FileCachedMarketConstituentsProvider,
)


class FakeMarketConstituentsProvider:
    def __init__(self, symbols_by_market: dict[str, list[str]]):
        self._symbols_by_market = symbols_by_market
        self.calls: list[str] = []

    def get_symbols(self, market_id: str) -> list[str]:
        self.calls.append(market_id)
        return self._symbols_by_market[market_id]


class FailingMarketConstituentsProvider:
    def get_symbols(self, market_id: str) -> list[str]:
        raise RuntimeError("source is down")


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "markets"


class TestFileCachedMarketConstituentsProvider:
    def test_empty_cache_fetches_and_persists(self, data_dir):
        inner = FakeMarketConstituentsProvider({"sp500": ["AAPL", "MSFT"]})
        provider = FileCachedMarketConstituentsProvider(inner=inner, data_dir=data_dir)

        result = provider.get_symbols("sp500")

        assert result == ["AAPL", "MSFT"]
        assert inner.calls == ["sp500"]
        assert (data_dir / "sp500.json").exists()

    def test_a_fresh_cache_is_served_without_refetching(self, data_dir):
        inner = FakeMarketConstituentsProvider({"sp500": ["AAPL", "MSFT"]})
        provider = FileCachedMarketConstituentsProvider(inner=inner, data_dir=data_dir)
        provider.get_symbols("sp500")

        result = provider.get_symbols("sp500")

        assert result == ["AAPL", "MSFT"]
        assert len(inner.calls) == 1  # no second fetch

    def test_a_stale_cache_triggers_a_refetch(self, data_dir):
        inner = FakeMarketConstituentsProvider({"sp500": ["AAPL", "MSFT", "GOOGL"]})
        provider = FileCachedMarketConstituentsProvider(
            inner=inner, data_dir=data_dir, ttl=timedelta(seconds=-1)
        )
        provider.get_symbols("sp500")

        result = provider.get_symbols("sp500")

        assert result == ["AAPL", "MSFT", "GOOGL"]
        assert len(inner.calls) == 2

    def test_different_markets_are_cached_separately(self, data_dir):
        inner = FakeMarketConstituentsProvider({"sp500": ["AAPL"], "nse500": ["RELIANCE.NS"]})
        provider = FileCachedMarketConstituentsProvider(inner=inner, data_dir=data_dir)

        provider.get_symbols("sp500")
        provider.get_symbols("nse500")

        assert (data_dir / "sp500.json").exists()
        assert (data_dir / "nse500.json").exists()

    def test_a_failed_refetch_falls_back_to_the_last_cached_list(self, data_dir):
        good_inner = FakeMarketConstituentsProvider({"sp500": ["AAPL", "MSFT"]})
        provider = FileCachedMarketConstituentsProvider(
            inner=good_inner, data_dir=data_dir, ttl=timedelta(seconds=-1)
        )
        provider.get_symbols("sp500")

        failing_provider = FileCachedMarketConstituentsProvider(
            inner=FailingMarketConstituentsProvider(), data_dir=data_dir, ttl=timedelta(seconds=-1)
        )
        result = failing_provider.get_symbols("sp500")

        assert result == ["AAPL", "MSFT"]

    def test_a_failed_fetch_with_no_cache_at_all_propagates(self, data_dir):
        provider = FileCachedMarketConstituentsProvider(
            inner=FailingMarketConstituentsProvider(), data_dir=data_dir
        )

        with pytest.raises(RuntimeError):
            provider.get_symbols("sp500")

    def test_cache_persists_across_provider_instances(self, data_dir):
        inner = FakeMarketConstituentsProvider({"sp500": ["AAPL"]})
        FileCachedMarketConstituentsProvider(inner=inner, data_dir=data_dir).get_symbols("sp500")

        second_inner = FakeMarketConstituentsProvider({})  # would KeyError if actually called
        second_provider = FileCachedMarketConstituentsProvider(inner=second_inner, data_dir=data_dir)
        result = second_provider.get_symbols("sp500")

        assert result == ["AAPL"]
        assert second_inner.calls == []
