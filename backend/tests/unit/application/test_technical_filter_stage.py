from datetime import date, datetime, timezone

import pytest

from screener.application.analytics_cache import DailyAnalytics
from screener.application.technical_filter_stage import TechnicalFilterStage
from screener.domain.entities import Stock

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_stock(symbol: str, price: float) -> Stock:
    return Stock(
        symbol=symbol,
        name=f"{symbol} Inc.",
        sector="Technology",
        price=price,
        pe_ratio=15.0,
        market_cap=1e9,
        dividend_yield=0.01,
        as_of=AS_OF,
        is_stale=False,
    )


class FakeAnalyticsCache:
    def __init__(self, analytics_by_symbol: dict[str, DailyAnalytics]):
        self._analytics_by_symbol = analytics_by_symbol

    def get(self, symbol: str, on_date: date) -> DailyAnalytics:
        return self._analytics_by_symbol[symbol]


class TestTechnicalFilterStage:
    def test_keeps_stocks_priced_above_the_50_day_sma(self):
        cache = FakeAnalyticsCache(
            {
                "ABOVE": DailyAnalytics(symbol="ABOVE", date=date.today(), sma_50=100.0, sma_200=None),
                "BELOW": DailyAnalytics(symbol="BELOW", date=date.today(), sma_50=100.0, sma_200=None),
            }
        )
        stage = TechnicalFilterStage(analytics_cache=cache)
        stocks = [make_stock("ABOVE", price=110.0), make_stock("BELOW", price=90.0)]

        result = stage.apply(stocks, above_sma_window=50)

        assert [s.symbol for s in result] == ["ABOVE"]

    def test_uses_the_200_day_sma_when_requested(self):
        cache = FakeAnalyticsCache(
            {"AAPL": DailyAnalytics(symbol="AAPL", date=date.today(), sma_50=None, sma_200=150.0)}
        )
        stage = TechnicalFilterStage(analytics_cache=cache)

        result = stage.apply([make_stock("AAPL", price=160.0)], above_sma_window=200)

        assert [s.symbol for s in result] == ["AAPL"]

    def test_excludes_a_stock_with_insufficient_sma_history(self):
        cache = FakeAnalyticsCache(
            {"NEW": DailyAnalytics(symbol="NEW", date=date.today(), sma_50=None, sma_200=None)}
        )
        stage = TechnicalFilterStage(analytics_cache=cache)

        result = stage.apply([make_stock("NEW", price=50.0)], above_sma_window=50)

        assert result == []

    def test_rejects_an_unsupported_window(self):
        stage = TechnicalFilterStage(analytics_cache=FakeAnalyticsCache({}))

        with pytest.raises(ValueError):
            stage.apply([make_stock("AAPL", price=100.0)], above_sma_window=20)
