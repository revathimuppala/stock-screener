from datetime import datetime, timezone

from fastapi.testclient import TestClient

from screener.api.dependencies import get_screening_service
from screener.api.main import app
from screener.application.ports import ProviderBatchResult
from screener.application.screening_service import ScreeningService
from screener.domain.entities import Stock

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


class StubProvider:
    def __init__(self, stocks):
        self._stocks = stocks

    def get_quotes(self, symbols):
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=[])


def _client() -> TestClient:
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        sector="Technology",
        price=190.0,
        pe_ratio=15.0,
        market_cap=3e12,
        dividend_yield=0.005,
        as_of=AS_OF,
        is_stale=False,
    )
    service = ScreeningService(provider=StubProvider([stock]), universe=["AAPL"])
    app.dependency_overrides[get_screening_service] = lambda: service
    return TestClient(app)


class TestScreenerExport:
    def test_export_returns_csv_content_type(self):
        client = _client()
        response = client.get("/api/v1/screener/export")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")

    def test_export_contains_header_and_row(self):
        client = _client()
        response = client.get("/api/v1/screener/export")

        lines = response.text.strip().splitlines()
        assert lines[0].split(",")[0] == "symbol"
        assert any(line.startswith("AAPL,") for line in lines[1:])

    def test_export_respects_query_params(self):
        client = _client()
        response = client.get("/api/v1/screener/export", params={"pe_min": 100})

        lines = response.text.strip().splitlines()
        assert len(lines) == 1  # header only, AAPL's P/E is 15
