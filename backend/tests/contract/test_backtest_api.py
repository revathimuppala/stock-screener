from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from screener.api.dependencies import get_backtest_job_store, get_backtest_service
from screener.api.main import app
from screener.application.backtest_service import BacktestService
from screener.application.ports import ProviderBatchResult
from screener.domain.entities import PriceBar, Stock
from screener.infrastructure.backtest_job_store import BacktestJobStore

AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)


class StubProvider:
    def __init__(self, stocks):
        self._stocks = stocks

    def get_quotes(self, symbols):
        return ProviderBatchResult(stocks=self._stocks, excluded_symbols=[])


class StubPriceHistoryProvider:
    def __init__(self, bars_by_symbol):
        self._bars_by_symbol = bars_by_symbol

    def get_history(self, symbol, start, end):
        return [b for b in self._bars_by_symbol.get(symbol, []) if start <= b.date <= end]


def _client(tmp_path):
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        sector="Technology",
        price=100.0,
        pe_ratio=15.0,
        market_cap=1e9,
        dividend_yield=0.01,
        as_of=AS_OF,
        is_stale=False,
    )
    bars = [PriceBar(date=date(2026, 1, d), close=100.0 + d) for d in range(1, 6)]
    service = BacktestService(
        stock_provider=StubProvider([stock]),
        price_history_provider=StubPriceHistoryProvider({"AAPL": bars}),
        universe=["AAPL"],
    )
    app.dependency_overrides[get_backtest_service] = lambda: service
    app.dependency_overrides[get_backtest_job_store] = lambda: BacktestJobStore(data_dir=tmp_path / "backtesting")
    return TestClient(app)


class TestBacktestApi:
    def test_starting_a_backtest_returns_202_with_a_job_id(self, tmp_path):
        client = _client(tmp_path)

        response = client.post(
            "/api/v1/backtest",
            json={
                "criteria": {"pe_max": 20},
                "start_date": "2026-01-01",
                "end_date": "2026-01-05",
                "holding_period_days": 1,
            },
        )

        assert response.status_code == 202
        assert response.json()["status"] == "pending"
        assert "backtest_id" in response.json()

    def test_polling_after_completion_returns_the_full_result(self, tmp_path):
        client = _client(tmp_path)
        start = client.post(
            "/api/v1/backtest",
            json={
                "criteria": {"pe_max": 20},
                "start_date": "2026-01-01",
                "end_date": "2026-01-05",
                "holding_period_days": 1,
            },
        )
        backtest_id = start.json()["backtest_id"]

        poll = client.get(f"/api/v1/backtest/{backtest_id}")

        assert poll.status_code == 200
        body = poll.json()
        assert body["status"] == "completed"
        assert "timeline" in body
        assert "summary" in body

    def test_query_based_backtest_works_too(self, tmp_path):
        client = _client(tmp_path)
        start = client.post(
            "/api/v1/backtest",
            json={
                "query": "pe < 20",
                "start_date": "2026-01-01",
                "end_date": "2026-01-05",
                "holding_period_days": 1,
            },
        )

        poll = client.get(f"/api/v1/backtest/{start.json()['backtest_id']}")
        assert poll.json()["status"] == "completed"

    def test_malformed_query_is_rejected_before_scheduling(self, tmp_path):
        client = _client(tmp_path)

        response = client.post(
            "/api/v1/backtest",
            json={
                "query": "not_a_field < 20",
                "start_date": "2026-01-01",
                "end_date": "2026-01-05",
                "holding_period_days": 1,
            },
        )

        assert response.status_code == 400

    def test_polling_unknown_job_is_404(self, tmp_path):
        client = _client(tmp_path)

        response = client.get("/api/v1/backtest/does-not-exist")

        assert response.status_code == 404

    def test_both_criteria_and_query_is_422(self, tmp_path):
        client = _client(tmp_path)

        response = client.post(
            "/api/v1/backtest",
            json={
                "criteria": {"pe_max": 20},
                "query": "pe < 20",
                "start_date": "2026-01-01",
                "end_date": "2026-01-05",
                "holding_period_days": 1,
            },
        )

        assert response.status_code == 422
