from datetime import datetime, timezone

from fastapi.testclient import TestClient

from screener.api.dependencies import (
    get_market_constituents_provider,
    get_screen_job_store,
    get_screening_service,
)
from screener.api.main import app
from screener.application.ports import ProviderBatchResult
from screener.application.screening_service import ScreeningService
from screener.domain.entities import Stock
from screener.infrastructure.backtest_job_store import BacktestJobStore

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


class StubProvider:
    def __init__(self, stocks):
        self._stocks = stocks
        self.requested_symbols: list[list[str]] = []

    def get_quotes(self, symbols):
        self.requested_symbols.append(list(symbols))
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=[])


class StubMarketConstituentsProvider:
    def __init__(self, symbols_by_market: dict[str, list[str]]):
        self._symbols_by_market = symbols_by_market

    def get_symbols(self, market_id: str) -> list[str]:
        return self._symbols_by_market[market_id]


def _stock(symbol: str) -> Stock:
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


def _client(tmp_path, stocks=None, symbols_by_market=None):
    provider = StubProvider(stocks if stocks is not None else [_stock("RELIANCE.NS")])
    service = ScreeningService(provider=provider, universe=["AAPL"])
    market_provider = StubMarketConstituentsProvider(
        symbols_by_market or {"nse500": ["RELIANCE.NS", "TCS.NS"]}
    )
    app.dependency_overrides[get_screening_service] = lambda: service
    app.dependency_overrides[get_market_constituents_provider] = lambda: market_provider
    app.dependency_overrides[get_screen_job_store] = lambda: BacktestJobStore(
        data_dir=tmp_path / "screening"
    )
    client = TestClient(app)
    return client, provider


class TestScreenerJobsApi:
    def test_starting_a_job_returns_202_with_a_job_id(self, tmp_path):
        client, _ = _client(tmp_path)

        response = client.post(
            "/api/v1/screener/jobs", json={"market_id": "nse500", "criteria": {"pe_max": 20}}
        )

        assert response.status_code == 202
        assert response.json()["status"] == "pending"
        assert "screen_id" in response.json()

    def test_polling_after_completion_returns_results(self, tmp_path):
        client, provider = _client(tmp_path)
        start = client.post(
            "/api/v1/screener/jobs", json={"market_id": "nse500", "criteria": {"pe_max": 20}}
        )

        poll = client.get(f"/api/v1/screener/jobs/{start.json()['screen_id']}")

        assert poll.status_code == 200
        body = poll.json()
        assert body["status"] == "completed"
        assert body["screen_status"] == "ok"
        assert [s["symbol"] for s in body["results"]] == ["RELIANCE.NS"]
        # the market's constituent list was used as the universe
        assert provider.requested_symbols == [["RELIANCE.NS", "TCS.NS"]]

    def test_query_based_job_works_too(self, tmp_path):
        client, _ = _client(tmp_path)

        start = client.post("/api/v1/screener/jobs", json={"market_id": "nse500", "query": "pe < 20"})
        poll = client.get(f"/api/v1/screener/jobs/{start.json()['screen_id']}")

        assert poll.json()["status"] == "completed"
        assert poll.json()["screen_status"] == "ok"

    def test_explicit_symbols_win_over_the_market(self, tmp_path):
        client, provider = _client(tmp_path)

        client.post(
            "/api/v1/screener/jobs",
            json={"market_id": "nse500", "criteria": {"pe_max": 20}, "symbols": ["CUSTOM.NS"]},
        )

        assert provider.requested_symbols == [["CUSTOM.NS"]]

    def test_unknown_market_id_is_rejected(self, tmp_path):
        client, _ = _client(tmp_path)

        response = client.post(
            "/api/v1/screener/jobs", json={"market_id": "dow30", "criteria": {"pe_max": 20}}
        )

        assert response.status_code == 400

    def test_malformed_query_is_rejected_before_scheduling(self, tmp_path):
        client, _ = _client(tmp_path)

        response = client.post(
            "/api/v1/screener/jobs", json={"market_id": "nse500", "query": "not_a_field < 20"}
        )

        assert response.status_code == 400

    def test_both_criteria_and_query_is_422(self, tmp_path):
        client, _ = _client(tmp_path)

        response = client.post(
            "/api/v1/screener/jobs",
            json={"market_id": "nse500", "criteria": {"pe_max": 20}, "query": "pe < 20"},
        )

        assert response.status_code == 422

    def test_polling_unknown_job_is_404(self, tmp_path):
        client, _ = _client(tmp_path)

        response = client.get("/api/v1/screener/jobs/does-not-exist")

        assert response.status_code == 404

    def test_a_provider_failure_marks_the_job_failed_not_completed(self, tmp_path):
        class FailingProvider:
            def get_quotes(self, symbols):
                raise RuntimeError("boom")

        service = ScreeningService(provider=FailingProvider(), universe=["AAPL"])
        market_provider = StubMarketConstituentsProvider({"nse500": ["RELIANCE.NS"]})
        app.dependency_overrides[get_screening_service] = lambda: service
        app.dependency_overrides[get_market_constituents_provider] = lambda: market_provider
        app.dependency_overrides[get_screen_job_store] = lambda: BacktestJobStore(
            data_dir=tmp_path / "screening"
        )
        client = TestClient(app)

        start = client.post(
            "/api/v1/screener/jobs", json={"market_id": "nse500", "criteria": {"pe_max": 20}}
        )
        poll = client.get(f"/api/v1/screener/jobs/{start.json()['screen_id']}")

        assert poll.json()["status"] == "failed"
        assert "boom" in poll.json()["error"]
