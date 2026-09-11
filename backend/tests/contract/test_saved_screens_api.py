from datetime import datetime, timezone

from fastapi.testclient import TestClient

from screener.api.dependencies import get_saved_screen_service, get_screening_service
from screener.api.main import app
from screener.application.ports import ProviderBatchResult
from screener.application.saved_screen_service import SavedScreenService
from screener.application.screening_service import ScreeningService
from screener.domain.entities import Stock
from screener.domain.universe import UNIVERSE

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


class StubProvider:
    def __init__(self, stocks=None):
        self._stocks = stocks or []

    def get_quotes(self, symbols):
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=[])


class InMemorySavedScreenRepository:
    def __init__(self):
        self._screens = {}

    def save(self, screen):
        self._screens[screen.id] = screen

    def list(self):
        return list(self._screens.values())

    def get(self, screen_id):
        return self._screens.get(screen_id)

    def delete(self, screen_id):
        self._screens.pop(screen_id, None)


def _client() -> TestClient:
    service = SavedScreenService(repository=InMemorySavedScreenRepository())
    app.dependency_overrides[get_saved_screen_service] = lambda: service
    stub_stock = Stock(
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
    screening_service = ScreeningService(provider=StubProvider([stub_stock]), universe=UNIVERSE)
    app.dependency_overrides[get_screening_service] = lambda: screening_service
    return TestClient(app)


class TestSavedScreensApi:
    def test_starts_empty(self):
        client = _client()
        response = client.get("/api/v1/screens")
        assert response.status_code == 200
        assert response.json() == {"screens": []}

    def test_save_criteria_screen_then_list(self):
        client = _client()
        response = client.post(
            "/api/v1/screens",
            json={"name": "Cheap tech", "criteria": {"pe_max": 20, "sector": "Technology"}},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Cheap tech"
        assert body["criteria"]["pe_max"] == 20
        assert body["query"] is None

        list_response = client.get("/api/v1/screens")
        assert len(list_response.json()["screens"]) == 1

    def test_save_query_screen(self):
        client = _client()
        response = client.post(
            "/api/v1/screens", json={"name": "DSL screen", "query": 'pe < 20'}
        )
        assert response.status_code == 201
        assert response.json()["query"] == "pe < 20"
        assert response.json()["criteria"] is None

    def test_save_with_both_criteria_and_query_is_422(self):
        client = _client()
        response = client.post(
            "/api/v1/screens",
            json={"name": "Bad", "criteria": {"pe_max": 20}, "query": "pe < 20"},
        )
        assert response.status_code == 422

    def test_save_with_neither_is_422(self):
        client = _client()
        response = client.post("/api/v1/screens", json={"name": "Bad"})
        assert response.status_code == 422

    def test_delete(self):
        client = _client()
        create = client.post("/api/v1/screens", json={"name": "X", "criteria": {"pe_max": 20}})
        screen_id = create.json()["id"]

        delete_response = client.delete(f"/api/v1/screens/{screen_id}")

        assert delete_response.status_code == 204
        assert client.get("/api/v1/screens").json()["screens"] == []

    def test_run_a_saved_criteria_screen(self):
        client = _client()
        create = client.post("/api/v1/screens", json={"name": "X", "criteria": {}})
        screen_id = create.json()["id"]

        run_response = client.get(f"/api/v1/screens/{screen_id}/run")

        assert run_response.status_code == 200
        assert "results" in run_response.json()

    def test_run_missing_screen_is_404(self):
        client = _client()
        response = client.get("/api/v1/screens/missing/run")
        assert response.status_code == 404
