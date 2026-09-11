from datetime import datetime, timezone

import pytest

from screener.infrastructure.exceptions import ProviderDataError, TransientProviderError
from screener.infrastructure.resilient_provider import ResilientStockDataProvider
from screener.domain.entities import Stock

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_stock(symbol: str, **overrides) -> Stock:
    defaults = dict(
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
    defaults.update(overrides)
    return Stock(**defaults)


class ScriptedFetcher:
    """Fake single-symbol fetcher: pop the next scripted outcome per call."""

    def __init__(self, script: dict[str, list]):
        self._script = {symbol: list(outcomes) for symbol, outcomes in script.items()}
        self.calls: list[str] = []

    def fetch(self, symbol: str) -> Stock:
        self.calls.append(symbol)
        outcome = self._script[symbol].pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class TestRetrySucceedsEventually:
    def test_retries_transient_failures_then_succeeds(self):
        fetcher = ScriptedFetcher(
            {
                "AAPL": [
                    TransientProviderError("timeout"),
                    TransientProviderError("timeout"),
                    make_stock("AAPL"),
                ]
            }
        )
        provider = ResilientStockDataProvider(fetcher=fetcher, retry_wait_seconds=0)

        result = provider.get_quotes(["AAPL"])

        assert [s.symbol for s in result.stocks] == ["AAPL"]
        assert result.stocks[0].is_stale is False
        assert result.excluded_symbols == []
        assert len(fetcher.calls) == 3

    def test_data_errors_are_not_retried(self):
        fetcher = ScriptedFetcher({"BADSYM": [ProviderDataError("unknown symbol")]})
        provider = ResilientStockDataProvider(fetcher=fetcher, retry_wait_seconds=0)

        result = provider.get_quotes(["BADSYM"])

        assert result.stocks == []
        assert result.excluded_symbols == ["BADSYM"]
        assert len(fetcher.calls) == 1


class TestCircuitBreakerAndCacheFallback:
    def test_exhausted_retries_with_no_cache_excludes_symbol(self):
        fetcher = ScriptedFetcher({"AAPL": [TransientProviderError("down")] * 3})
        provider = ResilientStockDataProvider(fetcher=fetcher, retry_wait_seconds=0)

        result = provider.get_quotes(["AAPL"])

        assert result.stocks == []
        assert result.excluded_symbols == ["AAPL"]

    def test_falls_back_to_cache_when_fetch_fails_after_a_prior_success(self):
        fetcher = ScriptedFetcher(
            {
                "AAPL": [
                    make_stock("AAPL"),
                    *([TransientProviderError("down")] * 3),
                ]
            }
        )
        provider = ResilientStockDataProvider(fetcher=fetcher, retry_wait_seconds=0)

        first = provider.get_quotes(["AAPL"])
        assert first.stocks[0].is_stale is False

        second = provider.get_quotes(["AAPL"])

        assert second.excluded_symbols == []
        assert second.stocks[0].symbol == "AAPL"
        assert second.stocks[0].is_stale is True

    def test_breaker_opens_after_threshold_and_skips_calling_fetcher(self):
        script = {"AAPL": [TransientProviderError("down")] * 100}
        fetcher = ScriptedFetcher(script)
        provider = ResilientStockDataProvider(
            fetcher=fetcher, retry_wait_seconds=0, breaker_fail_max=2, breaker_reset_seconds=60
        )

        provider.get_quotes(["AAPL"])  # 3 calls, 1st breaker failure
        provider.get_quotes(["AAPL"])  # 3 calls, 2nd breaker failure -> breaker opens

        calls_before = len(fetcher.calls)
        result = provider.get_quotes(["AAPL"])  # breaker open: should not call fetcher at all

        assert len(fetcher.calls) == calls_before
        assert result.excluded_symbols == ["AAPL"]
