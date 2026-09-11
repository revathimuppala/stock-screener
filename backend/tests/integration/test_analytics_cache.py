from datetime import date, timedelta

import pytest

from screener.domain.entities import PriceBar
from screener.application.analytics_cache import AnalyticsCache


class FakePriceHistoryProvider:
    def __init__(self, bars: list[PriceBar]):
        self._bars = bars
        self.calls = 0

    def get_history(self, symbol, start, end):
        self.calls += 1
        return [b for b in self._bars if start <= b.date <= end]


def consecutive_bars(count: int, end: date, close: float = 100.0) -> list[PriceBar]:
    return [PriceBar(date=end - timedelta(days=count - 1 - i), close=close) for i in range(count)]


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "analytics"


class TestAnalyticsCache:
    def test_computes_sma_50_when_enough_history(self, data_dir):
        on_date = date(2020, 1, 1)  # safely in the past
        bars = consecutive_bars(60, on_date, close=10.0)
        provider = FakePriceHistoryProvider(bars)
        cache = AnalyticsCache(price_history=provider, data_dir=data_dir)

        analytics = cache.get("AAPL", on_date)

        assert analytics.sma_50 == pytest.approx(10.0)

    def test_none_sma_when_insufficient_history(self, data_dir):
        on_date = date(2020, 1, 1)
        bars = consecutive_bars(10, on_date)
        provider = FakePriceHistoryProvider(bars)
        cache = AnalyticsCache(price_history=provider, data_dir=data_dir)

        analytics = cache.get("AAPL", on_date)

        assert analytics.sma_50 is None
        assert analytics.sma_200 is None

    def test_past_date_result_is_persisted_and_not_recomputed(self, data_dir):
        on_date = date(2020, 1, 1)
        bars = consecutive_bars(60, on_date, close=10.0)
        provider = FakePriceHistoryProvider(bars)
        cache = AnalyticsCache(price_history=provider, data_dir=data_dir)

        cache.get("AAPL", on_date)
        assert provider.calls == 1

        cache.get("AAPL", on_date)
        assert provider.calls == 1  # served from the cache file, no second history fetch

        path = data_dir / "AAPL" / f"{on_date.strftime('%Y%m%d')}.csv"
        assert path.exists()

    def test_todays_date_is_never_persisted(self, data_dir):
        today = date.today()
        bars = consecutive_bars(60, today, close=10.0)
        provider = FakePriceHistoryProvider(bars)
        cache = AnalyticsCache(price_history=provider, data_dir=data_dir)

        cache.get("AAPL", today)

        path = data_dir / "AAPL" / f"{today.strftime('%Y%m%d')}.csv"
        assert not path.exists()
