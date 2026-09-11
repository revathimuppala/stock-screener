from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from screener.api.dependencies import get_company_detail_service
from screener.api.main import app
from screener.application.company_detail_service import CompanyDetailService
from screener.application.ports import ProviderBatchResult
from screener.domain.entities import (
    FilingLink,
    QuarterlyFinancials,
    RawFinancials,
    Stock,
)

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


class StubStockDataProvider:
    def __init__(self, stocks):
        self._stocks = stocks

    def get_quotes(self, symbols):
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=[])


class StubFinancialsProvider:
    def __init__(self, financials_by_symbol):
        self._financials_by_symbol = financials_by_symbol

    def get_financials(self, symbol):
        return self._financials_by_symbol.get(symbol)


class StubFilingLinkProvider:
    def __init__(self, filings_by_symbol):
        self._filings_by_symbol = filings_by_symbol

    def get_filing_links(self, symbol):
        return self._filings_by_symbol.get(symbol, [])


def _stock(symbol: str) -> Stock:
    return Stock(
        symbol=symbol,
        name="Apple Inc.",
        sector="Technology",
        price=190.0,
        pe_ratio=15.0,
        market_cap=3e12,
        dividend_yield=0.005,
        as_of=AS_OF,
        is_stale=False,
        industry="Consumer Electronics",
        business_summary="Apple designs and sells consumer electronics.",
    )


def _client(
    stocks=None, financials_by_symbol=None, filings_by_symbol=None
) -> TestClient:
    service = CompanyDetailService(
        stock_data_provider=StubStockDataProvider(stocks or [_stock("AAPL")]),
        financials_provider=StubFinancialsProvider(financials_by_symbol or {}),
        filing_link_provider=StubFilingLinkProvider(filings_by_symbol or {}),
    )
    app.dependency_overrides[get_company_detail_service] = lambda: service
    return TestClient(app)


class TestCompaniesApi:
    def test_returns_the_composed_company_detail(self):
        financials = RawFinancials(
            symbol="AAPL",
            total_debt=50.0,
            total_assets=200.0,
            quarters=[
                QuarterlyFinancials(
                    period_end=date(2026, 6, 30),
                    revenue=100.0,
                    ebit=20.0,
                    ebitda=25.0,
                    net_income=15.0,
                    diluted_eps=1.0,
                    operating_cash_flow=18.0,
                    free_cash_flow=12.0,
                )
            ],
            shareholding=None,
        )
        filings = [FilingLink(form_type="10-K", filed_date=date(2026, 2, 1), url="https://sec.gov/x")]
        client = _client(financials_by_symbol={"AAPL": financials}, filings_by_symbol={"AAPL": filings})

        response = client.get("/api/v1/companies/AAPL")

        assert response.status_code == 200
        body = response.json()
        assert body["symbol"] == "AAPL"
        assert body["profile"]["business_summary"].startswith("Apple designs")
        assert body["quarters"][0]["revenue"] == 100.0
        assert body["filings"][0]["form_type"] == "10-K"

    def test_uppercases_the_symbol_path_param(self):
        client = _client(stocks=[_stock("AAPL")])

        response = client.get("/api/v1/companies/aapl")

        assert response.status_code == 200
        assert response.json()["symbol"] == "AAPL"

    def test_returns_404_for_an_unresolvable_symbol(self):
        client = _client(stocks=[])

        response = client.get("/api/v1/companies/ZZZZ")

        assert response.status_code == 404
