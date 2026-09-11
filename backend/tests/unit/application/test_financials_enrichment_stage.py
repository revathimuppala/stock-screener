from datetime import date, datetime, timezone

from screener.application.financials_enrichment_stage import FinancialsEnrichmentStage
from screener.domain.entities import QuarterlyFinancials, RawFinancials, Stock

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_stock(symbol: str) -> Stock:
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


def make_quarter(**overrides) -> QuarterlyFinancials:
    defaults = dict(
        period_end=date(2026, 6, 30),
        revenue=100.0,
        ebit=20.0,
        ebitda=25.0,
        net_income=15.0,
        diluted_eps=1.0,
        operating_cash_flow=18.0,
        free_cash_flow=12.0,
    )
    defaults.update(overrides)
    return QuarterlyFinancials(**defaults)


class FakeFinancialsProvider:
    def __init__(self, financials_by_symbol: dict[str, RawFinancials | None]):
        self._financials_by_symbol = financials_by_symbol

    def get_financials(self, symbol: str) -> RawFinancials | None:
        return self._financials_by_symbol.get(symbol)


class TestFinancialsEnrichmentStage:
    def test_computes_debt_to_assets_and_cfo_to_operating_profit(self):
        financials = RawFinancials(
            symbol="AAPL",
            total_debt=50.0,
            total_assets=200.0,
            quarters=[make_quarter(operating_cash_flow=18.0, ebit=20.0)],
            shareholding=None,
        )
        stage = FinancialsEnrichmentStage(FakeFinancialsProvider({"AAPL": financials}))

        [enriched] = stage.enrich([make_stock("AAPL")])

        assert enriched.debt_to_assets == 0.25
        assert enriched.cfo_to_operating_profit == 0.9

    def test_missing_financials_leaves_fields_none(self):
        stage = FinancialsEnrichmentStage(FakeFinancialsProvider({"AAPL": None}))

        [enriched] = stage.enrich([make_stock("AAPL")])

        assert enriched.debt_to_assets is None
        assert enriched.cfo_to_operating_profit is None
        assert enriched.symbol == "AAPL"  # stock otherwise untouched

    def test_no_quarters_leaves_cfo_ratio_none(self):
        financials = RawFinancials(
            symbol="AAPL", total_debt=50.0, total_assets=200.0, quarters=[], shareholding=None
        )
        stage = FinancialsEnrichmentStage(FakeFinancialsProvider({"AAPL": financials}))

        [enriched] = stage.enrich([make_stock("AAPL")])

        assert enriched.debt_to_assets == 0.25
        assert enriched.cfo_to_operating_profit is None

    def test_zero_ebit_does_not_raise_a_division_error(self):
        financials = RawFinancials(
            symbol="AAPL",
            total_debt=None,
            total_assets=None,
            quarters=[make_quarter(ebit=0.0, operating_cash_flow=18.0)],
            shareholding=None,
        )
        stage = FinancialsEnrichmentStage(FakeFinancialsProvider({"AAPL": financials}))

        [enriched] = stage.enrich([make_stock("AAPL")])

        assert enriched.cfo_to_operating_profit is None
