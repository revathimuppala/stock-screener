from fastapi.testclient import TestClient

from screener.api.dependencies import get_watchlist_service
from screener.api.main import app
from screener.application.watchlist_service import WatchlistService


class InMemoryWatchlistRepository:
    def __init__(self):
        self._symbols: list[str] = []

    def add(self, symbol: str) -> None:
        if symbol not in self._symbols:
            self._symbols.append(symbol)

    def remove(self, symbol: str) -> None:
        if symbol in self._symbols:
            self._symbols.remove(symbol)

    def list_symbols(self) -> list[str]:
        return list(self._symbols)


def _client() -> TestClient:
    service = WatchlistService(repository=InMemoryWatchlistRepository())
    app.dependency_overrides[get_watchlist_service] = lambda: service
    return TestClient(app)


class TestWatchlistApi:
    def test_starts_empty(self):
        client = _client()
        response = client.get("/api/v1/watchlist")
        assert response.status_code == 200
        assert response.json() == {"symbols": []}

    def test_add_then_get(self):
        client = _client()
        add_response = client.post("/api/v1/watchlist", json={"symbol": "aapl"})
        assert add_response.status_code == 201

        get_response = client.get("/api/v1/watchlist")
        assert get_response.json() == {"symbols": ["AAPL"]}

    def test_remove(self):
        client = _client()
        client.post("/api/v1/watchlist", json={"symbol": "AAPL"})

        delete_response = client.delete("/api/v1/watchlist/AAPL")

        assert delete_response.status_code == 204
        assert client.get("/api/v1/watchlist").json() == {"symbols": []}

    def test_add_missing_symbol_field_is_422(self):
        client = _client()
        response = client.post("/api/v1/watchlist", json={})
        assert response.status_code == 422
