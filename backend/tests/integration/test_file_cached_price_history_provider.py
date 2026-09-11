from datetime import date

import pytest

from screener.domain.entities import PriceBar
from screener.infrastructure.file_cached_price_history_provider import FileCachedPriceHistoryProvider


class FakePriceHistoryProvider:
    """Records every call so tests can assert exactly what range was
    actually fetched from the (expensive) underlying source."""

    def __init__(self, bars_by_symbol: dict[str, list[PriceBar]]):
        self._bars_by_symbol = bars_by_symbol
        self.calls: list[tuple[str, date, date]] = []

    def get_history(self, symbol: str, start: date, end: date) -> list[PriceBar]:
        self.calls.append((symbol, start, end))
        return [b for b in self._bars_by_symbol.get(symbol, []) if start <= b.date <= end]


def bars(*pairs: tuple[str, float]) -> list[PriceBar]:
    return [PriceBar(date=date.fromisoformat(d), close=c) for d, c in pairs]


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "returns"


class TestFileCachedPriceHistoryProvider:
    def test_empty_cache_fetches_and_persists_the_full_range(self, data_dir):
        inner = FakePriceHistoryProvider(
            {"AAPL": bars(("2026-01-01", 100.0), ("2026-01-02", 101.0), ("2026-01-03", 102.0))}
        )
        provider = FileCachedPriceHistoryProvider(inner=inner, data_dir=data_dir)

        result = provider.get_history("AAPL", date(2026, 1, 1), date(2026, 1, 3))

        assert [b.close for b in result] == [100.0, 101.0, 102.0]
        assert inner.calls == [("AAPL", date(2026, 1, 1), date(2026, 1, 3))]
        assert (data_dir / "AAPL" / "returns.csv").exists()

    def test_a_fully_covered_repeat_request_does_not_refetch(self, data_dir):
        inner = FakePriceHistoryProvider(
            {"AAPL": bars(("2026-01-01", 100.0), ("2026-01-02", 101.0), ("2026-01-03", 102.0))}
        )
        provider = FileCachedPriceHistoryProvider(inner=inner, data_dir=data_dir)
        provider.get_history("AAPL", date(2026, 1, 1), date(2026, 1, 3))

        result = provider.get_history("AAPL", date(2026, 1, 1), date(2026, 1, 2))

        assert [b.close for b in result] == [100.0, 101.0]
        assert len(inner.calls) == 1  # no second call to the underlying source

    def test_extending_the_range_forward_only_fetches_the_new_part(self, data_dir):
        inner = FakePriceHistoryProvider(
            {
                "AAPL": bars(
                    ("2026-01-01", 100.0),
                    ("2026-01-02", 101.0),
                    ("2026-01-03", 102.0),
                    ("2026-01-04", 103.0),
                )
            }
        )
        provider = FileCachedPriceHistoryProvider(inner=inner, data_dir=data_dir)
        provider.get_history("AAPL", date(2026, 1, 1), date(2026, 1, 2))

        result = provider.get_history("AAPL", date(2026, 1, 1), date(2026, 1, 4))

        assert [b.close for b in result] == [100.0, 101.0, 102.0, 103.0]
        assert inner.calls[1] == ("AAPL", date(2026, 1, 3), date(2026, 1, 4))

    def test_extending_the_range_backward_only_fetches_the_new_part(self, data_dir):
        inner = FakePriceHistoryProvider(
            {"AAPL": bars(("2026-01-01", 100.0), ("2026-01-02", 101.0), ("2026-01-03", 102.0))}
        )
        provider = FileCachedPriceHistoryProvider(inner=inner, data_dir=data_dir)
        provider.get_history("AAPL", date(2026, 1, 2), date(2026, 1, 3))

        result = provider.get_history("AAPL", date(2026, 1, 1), date(2026, 1, 3))

        assert [b.close for b in result] == [100.0, 101.0, 102.0]
        assert inner.calls[1] == ("AAPL", date(2026, 1, 1), date(2026, 1, 1))

    def test_cache_persists_across_provider_instances(self, data_dir):
        inner = FakePriceHistoryProvider({"AAPL": bars(("2026-01-01", 100.0), ("2026-01-02", 101.0))})
        FileCachedPriceHistoryProvider(inner=inner, data_dir=data_dir).get_history(
            "AAPL", date(2026, 1, 1), date(2026, 1, 2)
        )

        second_inner = FakePriceHistoryProvider({})  # would fail the test if actually called
        second_provider = FileCachedPriceHistoryProvider(inner=second_inner, data_dir=data_dir)
        result = second_provider.get_history("AAPL", date(2026, 1, 1), date(2026, 1, 2))

        assert [b.close for b in result] == [100.0, 101.0]
        assert second_inner.calls == []

    def test_different_symbols_are_cached_separately(self, data_dir):
        inner = FakePriceHistoryProvider(
            {"AAPL": bars(("2026-01-01", 100.0)), "MSFT": bars(("2026-01-01", 200.0))}
        )
        provider = FileCachedPriceHistoryProvider(inner=inner, data_dir=data_dir)

        provider.get_history("AAPL", date(2026, 1, 1), date(2026, 1, 1))
        provider.get_history("MSFT", date(2026, 1, 1), date(2026, 1, 1))

        assert (data_dir / "AAPL" / "returns.csv").exists()
        assert (data_dir / "MSFT" / "returns.csv").exists()
