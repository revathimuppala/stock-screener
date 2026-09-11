from datetime import date

from screener.domain.entities import PriceBar
from screener.infrastructure.exceptions import TransientProviderError
from screener.infrastructure.resilient_price_history_provider import ResilientPriceHistoryProvider


class ScriptedHistoryProvider:
    def __init__(self, script):
        self._script = list(script)
        self.calls: list[tuple[str, date, date]] = []

    def get_history(self, symbol, start, end):
        self.calls.append((symbol, start, end))
        outcome = self._script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class TestResilientPriceHistoryProvider:
    def test_passes_through_symbol_and_date_range(self):
        bars = [PriceBar(date=date(2026, 1, 1), close=100.0)]
        inner = ScriptedHistoryProvider([bars])
        provider = ResilientPriceHistoryProvider(inner, retry_wait_seconds=0)

        result = provider.get_history("AAPL", date(2026, 1, 1), date(2026, 1, 1))

        assert result == bars
        assert inner.calls == [("AAPL", date(2026, 1, 1), date(2026, 1, 1))]

    def test_retries_transient_failures_then_succeeds(self):
        bars = [PriceBar(date=date(2026, 1, 1), close=100.0)]
        inner = ScriptedHistoryProvider([TransientProviderError("down"), bars])
        provider = ResilientPriceHistoryProvider(inner, retry_wait_seconds=0)

        result = provider.get_history("AAPL", date(2026, 1, 1), date(2026, 1, 1))

        assert result == bars
        assert len(inner.calls) == 2

    def test_exhausted_retries_returns_empty_list(self):
        inner = ScriptedHistoryProvider([TransientProviderError("down")] * 3)
        provider = ResilientPriceHistoryProvider(inner, retry_wait_seconds=0)

        result = provider.get_history("AAPL", date(2026, 1, 1), date(2026, 1, 1))

        assert result == []
