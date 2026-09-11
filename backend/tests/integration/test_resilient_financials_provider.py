from screener.domain.entities import RawFinancials
from screener.infrastructure.exceptions import TransientProviderError
from screener.infrastructure.resilient_financials_provider import ResilientFinancialsProvider


class ScriptedFinancialsFetcher:
    def __init__(self, script):
        self._script = list(script)
        self.calls: list[str] = []

    def get_financials(self, symbol: str) -> RawFinancials:
        self.calls.append(symbol)
        outcome = self._script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_financials(symbol="AAPL") -> RawFinancials:
    return RawFinancials(symbol=symbol, total_debt=100.0, total_assets=500.0, quarters=[], shareholding=None)


class TestResilientFinancialsProvider:
    def test_passes_through_on_success(self):
        financials = make_financials()
        inner = ScriptedFinancialsFetcher([financials])
        provider = ResilientFinancialsProvider(inner, retry_wait_seconds=0)

        result = provider.get_financials("AAPL")

        assert result == financials

    def test_retries_then_succeeds(self):
        financials = make_financials()
        inner = ScriptedFinancialsFetcher([TransientProviderError("down"), financials])
        provider = ResilientFinancialsProvider(inner, retry_wait_seconds=0)

        result = provider.get_financials("AAPL")

        assert result == financials
        assert len(inner.calls) == 2

    def test_exhausted_retries_with_no_cache_returns_none(self):
        inner = ScriptedFinancialsFetcher([TransientProviderError("down")] * 3)
        provider = ResilientFinancialsProvider(inner, retry_wait_seconds=0)

        assert provider.get_financials("AAPL") is None

    def test_falls_back_to_cache_after_a_prior_success(self):
        financials = make_financials()
        inner = ScriptedFinancialsFetcher([financials, *([TransientProviderError("down")] * 3)])
        provider = ResilientFinancialsProvider(inner, retry_wait_seconds=0)

        provider.get_financials("AAPL")
        result = provider.get_financials("AAPL")

        assert result == financials
