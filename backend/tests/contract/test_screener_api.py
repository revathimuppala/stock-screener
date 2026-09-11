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
    def __init__(self, stocks, excluded=None):
        self._stocks = stocks
        self._excluded = excluded or []

    def get_quotes(self, symbols):
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=self._excluded)


def _client_with_stocks(stocks, excluded=None) -> TestClient:
    provider = StubProvider(stocks, excluded)
    service = ScreeningService(provider=provider, universe=[s.symbol for s in stocks] + (excluded or []))
    app.dependency_overrides[get_screening_service] = lambda: service
    return TestClient(app)


class TestScreenerEndpointHappyPath:
    def test_valid_payload_returns_ranked_results(self):
        client = _client_with_stocks([make_stock(symbol="AAPL", pe_ratio=15.0)])

        response = client.post("/api/v1/screener", json={"pe_min": 10, "pe_max": 20})

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["results"][0]["symbol"] == "AAPL"
        assert body["excluded_symbols"] == []

    def test_empty_body_screens_with_no_criteria(self):
        client = _client_with_stocks([make_stock(symbol="AAPL")])

        response = client.post("/api/v1/screener", json={})

        assert response.status_code == 200
        assert response.json()["results"][0]["symbol"] == "AAPL"

    def test_degraded_response_surfaces_excluded_symbols(self):
        client = _client_with_stocks([make_stock(symbol="AAPL")], excluded=["BAD"])

        response = client.post("/api/v1/screener", json={})

        body = response.json()
        assert body["status"] == "degraded"
        assert body["excluded_symbols"] == ["BAD"]


class TestScreenerEndpointValidation:
    def test_non_numeric_pe_min_returns_422(self):
        client = _client_with_stocks([make_stock()])

        response = client.post("/api/v1/screener", json={"pe_min": "not-a-number"})

        assert response.status_code == 422
