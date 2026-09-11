from fastapi.testclient import TestClient

from screener.api.main import app


class TestScreenerFieldsApi:
    def test_returns_the_dsl_field_allowlist(self):
        client = TestClient(app)

        response = client.get("/api/v1/screener/fields")

        assert response.status_code == 200
        body = response.json()
        names = {f["name"] for f in body["fields"]}
        assert "pe_ratio" in names
        assert "graham_value" in names
        # Deliberately excluded — see domain/dsl/fields.py's docstring.
        assert "rsi_14" not in names
        assert "sma_50" not in names

    def test_reports_field_types(self):
        client = TestClient(app)

        response = client.get("/api/v1/screener/fields")

        by_name = {f["name"]: f["type"] for f in response.json()["fields"]}
        assert by_name["symbol"] == "string"
        assert by_name["pe_ratio"] == "number"

    def test_includes_aliases(self):
        client = TestClient(app)

        response = client.get("/api/v1/screener/fields")

        assert response.json()["aliases"]["pe"] == "pe_ratio"
