from datetime import datetime, timezone

from fastapi.testclient import TestClient

from screener.api.dependencies import get_screening_service
from screener.api.main import app
from screener.application.ports import ProviderBatchResult
from screener.application.screening_service import ScreeningService
from screener.domain.entities import Stock

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_stock(**overrides) -> Stock:
    defaults = dict(
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
    defaults.update(overrides)
    return Stock(**defaults)


class StubProvider:
    def __init__(self, stocks):
        self._stocks = stocks

    def get_quotes(self, symbols):
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=[])


def _client(stocks) -> TestClient:
    service = ScreeningService(provider=StubProvider(stocks), universe=[s.symbol for s in stocks])
    app.dependency_overrides[get_screening_service] = lambda: service
    return TestClient(app)


class TestScreenerQueryApi:
    def test_valid_query_returns_ranked_results(self):
        client = _client([make_stock(symbol="AAPL", pe_ratio=15.0)])

        response = client.post("/api/v1/screener/query", json={"query": "pe < 20"})

        assert response.status_code == 200
        assert response.json()["results"][0]["symbol"] == "AAPL"

    def test_query_excludes_non_matching_stocks(self):
        client = _client([make_stock(symbol="CHEAP", pe_ratio=10.0), make_stock(symbol="PRICEY", pe_ratio=50.0)])

        response = client.post("/api/v1/screener/query", json={"query": "pe < 20"})

        symbols = [r["symbol"] for r in response.json()["results"]]
        assert symbols == ["CHEAP"]

    def test_malformed_query_returns_400_with_position(self):
        client = _client([make_stock()])

        response = client.post("/api/v1/screener/query", json={"query": "not_a_field < 20"})

        assert response.status_code == 400
        body = response.json()["detail"]
        assert "error" in body
        assert "position" in body

    def test_empty_query_returns_400(self):
        client = _client([make_stock()])

        response = client.post("/api/v1/screener/query", json={"query": ""})

        assert response.status_code == 400
