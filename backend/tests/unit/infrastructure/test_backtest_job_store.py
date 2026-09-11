import pytest

from screener.infrastructure.backtest_job_store import BacktestJobStore


@pytest.fixture
def store(tmp_path):
    return BacktestJobStore(data_dir=tmp_path / "backtesting")


class TestBacktestJobStore:
    def test_reading_a_missing_job_returns_none(self, store):
        assert store.read("missing") is None

    def test_write_then_read_round_trips(self, store):
        store.write("abc", {"status": "pending", "query": "pe < 20"})

        record = store.read("abc")

        assert record["status"] == "pending"
        assert record["query"] == "pe < 20"

    def test_write_overwrites_the_same_job(self, store):
        store.write("abc", {"status": "pending"})
        store.write("abc", {"status": "completed", "timeline": []})

        record = store.read("abc")

        assert record["status"] == "completed"
        assert record["timeline"] == []

    def test_persists_across_store_instances(self, tmp_path):
        data_dir = tmp_path / "backtesting"
        BacktestJobStore(data_dir=data_dir).write("abc", {"status": "completed"})

        second_store = BacktestJobStore(data_dir=data_dir)

        assert second_store.read("abc")["status"] == "completed"
