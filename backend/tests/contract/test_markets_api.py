from fastapi.testclient import TestClient

from screener.api.main import app


class TestMarketsApi:
    def test_returns_the_market_allowlist(self):
        client = TestClient(app)

        response = client.get("/api/v1/markets")

        assert response.status_code == 200
        ids = {m["id"] for m in response.json()["markets"]}
        assert ids == {"default", "sp500", "nasdaq100", "nse500", "bse500"}

    def test_default_market_is_listed_first(self):
        client = TestClient(app)

        response = client.get("/api/v1/markets")

        assert response.json()["markets"][0]["id"] == "default"
