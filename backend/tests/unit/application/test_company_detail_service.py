from datetime import date, datetime, timezone

from screener.application.company_detail_service import CompanyDetailService
from screener.application.ports import ProviderBatchResult
from screener.domain.entities import (
    FilingLink,
    InstitutionalHolder,
    QuarterlyFinancials,
    RawFinancials,
    ShareholdingPattern,
    Stock,
)

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_stock(symbol: str, industry: str | None = "Consumer Electronics", **overrides) -> Stock:
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
        industry=industry,
        business_summary=f"{symbol} makes things.",
    )
    defaults.update(overrides)
    return Stock(**defaults)


class FakeStockDataProvider:
    def __init__(self, stocks: list[Stock]):
        self._stocks = stocks
        self.requested_symbols: list[list[str]] = []

    def get_quotes(self, symbols: list[str]) -> ProviderBatchResult:
        self.requested_symbols.append(list(symbols))
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=[])


class FakeFinancialsProvider:
    def __init__(self, financials_by_symbol: dict[str, RawFinancials | None]):
        self._financials_by_symbol = financials_by_symbol

    def get_financials(self, symbol: str) -> RawFinancials | None:
        return self._financials_by_symbol.get(symbol)


class FakeFilingLinkProvider:
    def __init__(self, filings_by_symbol: dict[str, list[FilingLink]]):
        self._filings_by_symbol = filings_by_symbol

    def get_filing_links(self, symbol: str) -> list[FilingLink]:
        return self._filings_by_symbol.get(symbol, [])


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


class TestCompanyDetailService:
    def test_returns_none_for_a_symbol_the_provider_could_not_resolve(self):
        service = CompanyDetailService(
            FakeStockDataProvider([]), FakeFinancialsProvider({}), FakeFilingLinkProvider({})
        )

        assert service.get_detail("AAPL") is None

    def test_composes_profile_financials_and_filings(self):
        stocks = [make_stock("AAPL"), make_stock("MSFT", industry="Software")]
        financials = RawFinancials(
            symbol="AAPL",
            total_debt=50.0,
            total_assets=200.0,
            quarters=[make_quarter()],
            shareholding=ShareholdingPattern(
                insiders_pct=0.02, institutions_pct=0.6, top_holders=[InstitutionalHolder("Vanguard", 1e6, 0.01)]
            ),
        )
        filings = [FilingLink(form_type="10-K", filed_date=date(2026, 2, 1), url="https://sec.gov/x")]
        service = CompanyDetailService(
            FakeStockDataProvider(stocks),
            FakeFinancialsProvider({"AAPL": financials}),
            FakeFilingLinkProvider({"AAPL": filings}),
        )

        detail = service.get_detail("AAPL")

        assert detail.symbol == "AAPL"
        assert detail.profile.business_summary == "AAPL makes things."
        assert detail.profile.industry == "Consumer Electronics"
        assert detail.profile.order_backlog_note
        assert detail.quarters == [make_quarter()]
        assert detail.shareholding.institutions_pct == 0.6
        assert detail.filings == filings

    def test_competitors_are_other_universe_symbols_sharing_industry(self):
        stocks = [
            make_stock("AAPL", industry="Consumer Electronics"),
            make_stock("MSFT", industry="Software"),
            make_stock("HPQ", industry="Consumer Electronics"),
        ]
        service = CompanyDetailService(
            FakeStockDataProvider(stocks), FakeFinancialsProvider({}), FakeFilingLinkProvider({})
        )

        detail = service.get_detail("AAPL")

        assert detail.profile.competitors == ["HPQ"]

    def test_competitors_are_empty_when_target_industry_is_unknown(self):
        stocks = [
            make_stock("AAPL", industry=None),
            make_stock("MSFT", industry=None),
        ]
        service = CompanyDetailService(
            FakeStockDataProvider(stocks), FakeFinancialsProvider({}), FakeFilingLinkProvider({})
        )

        detail = service.get_detail("AAPL")

        assert detail.profile.competitors == []

    def test_missing_financials_yields_empty_quarters_and_no_shareholding(self):
        service = CompanyDetailService(
            FakeStockDataProvider([make_stock("AAPL")]),
            FakeFinancialsProvider({"AAPL": None}),
            FakeFilingLinkProvider({}),
        )

        detail = service.get_detail("AAPL")

        assert detail.quarters == []
        assert detail.shareholding is None

    def test_fetches_universe_plus_symbol_when_symbol_not_in_universe(self):
        provider = FakeStockDataProvider([make_stock("XYZ")])
        service = CompanyDetailService(
            provider, FakeFinancialsProvider({}), FakeFilingLinkProvider({})
        )

        service.get_detail("XYZ")

        assert "XYZ" in provider.requested_symbols[0]
        assert "AAPL" in provider.requested_symbols[0]  # part of UNIVERSE

    def test_does_not_refetch_symbol_already_in_universe(self):
        provider = FakeStockDataProvider([make_stock("AAPL")])
        service = CompanyDetailService(
            provider, FakeFinancialsProvider({}), FakeFilingLinkProvider({})
        )

        service.get_detail("AAPL")

        assert provider.requested_symbols[0].count("AAPL") == 1
