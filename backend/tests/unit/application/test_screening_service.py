from datetime import datetime, timezone

from screener.application.ports import ProviderBatchResult, StockDataProvider
from screener.application.screening_service import ScreeningService
from screener.domain.entities import ScreeningCriteria, Stock

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_stock(**overrides) -> Stock:
    defaults = dict(
        symbol="AAPL",
        name="Apple Inc.",
        sector="Technology",
        price=190.0,
        pe_ratio=15.0,
        market_cap=3_000_000_000_000.0,
        dividend_yield=0.005,
        as_of=AS_OF,
        is_stale=False,
    )
    defaults.update(overrides)
    return Stock(**defaults)


class FakeStockDataProvider:
    """Test double implementing the StockDataProvider port."""

    def __init__(self, stocks: list[Stock], excluded_symbols: list[str] | None = None):
        self._stocks = stocks
        self._excluded_symbols = excluded_symbols or []
        self.requested_symbols: list[list[str]] = []

    def get_quotes(self, symbols: list[str]) -> ProviderBatchResult:
        self.requested_symbols.append(list(symbols))
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=self._excluded_symbols)


def test_is_a_stock_data_provider() -> None:
    # sanity check that the fake satisfies the Protocol shape used by the service
    provider: StockDataProvider = FakeStockDataProvider([])
    assert provider.get_quotes([]) is not None


class TestScreeningServiceHappyPath:
    def test_ranks_by_dividend_yield_desc_then_pe_asc(self):
        stocks = [
            make_stock(symbol="LOW_YIELD", dividend_yield=0.01, pe_ratio=10.0),
            make_stock(symbol="HIGH_YIELD", dividend_yield=0.05, pe_ratio=30.0),
            make_stock(symbol="TIE_CHEAP", dividend_yield=0.05, pe_ratio=10.0),
        ]
        provider = FakeStockDataProvider(stocks)
        service = ScreeningService(provider=provider, universe=["LOW_YIELD", "HIGH_YIELD", "TIE_CHEAP"])

        result = service.screen(ScreeningCriteria())

        assert [s.symbol for s in result.results] == ["TIE_CHEAP", "HIGH_YIELD", "LOW_YIELD"]
        assert result.status == "ok"
        assert result.stale_symbols == []
        assert result.excluded_symbols == []

    def test_applies_criteria_before_ranking(self):
        stocks = [
            make_stock(symbol="CHEAP", pe_ratio=8.0),
            make_stock(symbol="MID", pe_ratio=15.0),
            make_stock(symbol="EXPENSIVE", pe_ratio=40.0),
        ]
        provider = FakeStockDataProvider(stocks)
        service = ScreeningService(provider=provider, universe=["CHEAP", "MID", "EXPENSIVE"])

        result = service.screen(ScreeningCriteria(pe_min=10, pe_max=20))

        assert [s.symbol for s in result.results] == ["MID"]

    def test_empty_result_is_ok_not_an_error(self):
        stocks = [make_stock(symbol="AAPL", pe_ratio=15.0)]
        provider = FakeStockDataProvider(stocks)
        service = ScreeningService(provider=provider, universe=["AAPL"])

        result = service.screen(ScreeningCriteria(pe_min=0, pe_max=0.01))

        assert result.status == "ok"
        assert result.results == []


class TestScreeningServiceDegradedModes:
    def test_excluded_symbol_is_reported_and_others_still_returned(self):
        stocks = [make_stock(symbol="GOOD", pe_ratio=15.0)]
        provider = FakeStockDataProvider(stocks, excluded_symbols=["BAD"])
        service = ScreeningService(provider=provider, universe=["GOOD", "BAD"])

        result = service.screen(ScreeningCriteria())

        assert result.status == "degraded"
        assert result.excluded_symbols == ["BAD"]
        assert [s.symbol for s in result.results] == ["GOOD"]

    def test_stale_stock_marks_batch_degraded(self):
        stocks = [make_stock(symbol="STALE_ONE", is_stale=True)]
        provider = FakeStockDataProvider(stocks)
        service = ScreeningService(provider=provider, universe=["STALE_ONE"])

        result = service.screen(ScreeningCriteria())

        assert result.status == "degraded"
        assert result.stale_symbols == ["STALE_ONE"]


class FakeTechnicalFilterStage:
    def __init__(self, symbols_that_pass: list[str] | None = None):
        self._symbols_that_pass = symbols_that_pass
        self.calls: list[int] = []
        self.enrich_calls = 0
        self.rsi_calls: list[tuple] = []

    def apply(self, stocks, above_sma_window):
        self.calls.append(above_sma_window)
        return [s for s in stocks if s.symbol in self._symbols_that_pass]

    def enrich(self, stocks):
        self.enrich_calls += 1
        return stocks

    def filter_by_rsi(self, stocks, rsi_min, rsi_max):
        self.rsi_calls.append((rsi_min, rsi_max))
        return [s for s in stocks if s.symbol in self._symbols_that_pass]


class FakeFinancialsEnrichmentStage:
    def __init__(self):
        self.enrich_calls = 0

    def enrich(self, stocks):
        self.enrich_calls += 1
        return stocks


class TestScreeningServiceTechnicalFilter:
    def test_above_sma_window_further_narrows_results(self):
        stocks = [make_stock(symbol="ABOVE"), make_stock(symbol="BELOW")]
        provider = FakeStockDataProvider(stocks)
        technical_stage = FakeTechnicalFilterStage(symbols_that_pass=["ABOVE"])
        service = ScreeningService(
            provider=provider, universe=["ABOVE", "BELOW"], technical_filter_stage=technical_stage
        )

        result = service.screen(ScreeningCriteria(above_sma_window=50))

        assert [s.symbol for s in result.results] == ["ABOVE"]
        assert technical_stage.calls == [50]

    def test_no_technical_filter_stage_configured_raises_when_requested(self):
        stocks = [make_stock(symbol="AAPL")]
        provider = FakeStockDataProvider(stocks)
        service = ScreeningService(provider=provider, universe=["AAPL"])

        try:
            service.screen(ScreeningCriteria(above_sma_window=50))
            assert False, "expected ValueError"
        except ValueError:
            pass

    def test_omitting_above_sma_window_never_touches_the_technical_stage(self):
        stocks = [make_stock(symbol="AAPL")]
        provider = FakeStockDataProvider(stocks)
        technical_stage = FakeTechnicalFilterStage(symbols_that_pass=[])
        service = ScreeningService(
            provider=provider, universe=["AAPL"], technical_filter_stage=technical_stage
        )

        result = service.screen(ScreeningCriteria())

        assert [s.symbol for s in result.results] == ["AAPL"]
        assert technical_stage.calls == []

    def test_enrich_is_always_called_when_a_stage_is_configured(self):
        stocks = [make_stock(symbol="AAPL")]
        provider = FakeStockDataProvider(stocks)
        technical_stage = FakeTechnicalFilterStage()
        service = ScreeningService(
            provider=provider, universe=["AAPL"], technical_filter_stage=technical_stage
        )

        service.screen(ScreeningCriteria())

        assert technical_stage.enrich_calls == 1

    def test_rsi_filter_narrows_results(self):
        stocks = [make_stock(symbol="OVERSOLD"), make_stock(symbol="NEUTRAL")]
        provider = FakeStockDataProvider(stocks)
        technical_stage = FakeTechnicalFilterStage(symbols_that_pass=["OVERSOLD"])
        service = ScreeningService(
            provider=provider, universe=["OVERSOLD", "NEUTRAL"], technical_filter_stage=technical_stage
        )

        result = service.screen(ScreeningCriteria(rsi_max=30.0))

        assert [s.symbol for s in result.results] == ["OVERSOLD"]
        assert technical_stage.rsi_calls == [(None, 30.0)]

    def test_financials_enrichment_is_always_called_when_configured(self):
        stocks = [make_stock(symbol="AAPL")]
        provider = FakeStockDataProvider(stocks)
        financials_stage = FakeFinancialsEnrichmentStage()
        service = ScreeningService(
            provider=provider, universe=["AAPL"], financials_enrichment_stage=financials_stage
        )

        service.screen(ScreeningCriteria())

        assert financials_stage.enrich_calls == 1


class TestScreeningServiceSymbolOverride:
    def test_symbols_in_criteria_override_the_default_universe(self):
        stocks = [make_stock(symbol="CUSTOM")]
        provider = FakeStockDataProvider(stocks)
        service = ScreeningService(provider=provider, universe=["AAPL", "MSFT"])

        result = service.screen(ScreeningCriteria(symbols=["CUSTOM"]))

        assert [s.symbol for s in result.results] == ["CUSTOM"]
        assert provider.requested_symbols == [["CUSTOM"]]

    def test_no_symbols_falls_back_to_the_default_universe(self):
        stocks = [make_stock(symbol="AAPL")]
        provider = FakeStockDataProvider(stocks)
        service = ScreeningService(provider=provider, universe=["AAPL"])

        result = service.screen(ScreeningCriteria(symbols=None))

        assert [s.symbol for s in result.results] == ["AAPL"]
