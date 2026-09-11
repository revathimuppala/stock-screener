from screener.infrastructure.sqlite_watchlist_repository import SqliteWatchlistRepository


def make_repo() -> SqliteWatchlistRepository:
    return SqliteWatchlistRepository(database_url="sqlite:///:memory:")


class TestSqliteWatchlistRepository:
    def test_starts_empty(self):
        repo = make_repo()
        assert repo.list_symbols() == []

    def test_add_then_list(self):
        repo = make_repo()
        repo.add("AAPL")
        assert repo.list_symbols() == ["AAPL"]

    def test_add_is_idempotent_at_the_storage_layer(self):
        repo = make_repo()
        repo.add("AAPL")
        repo.add("AAPL")
        assert repo.list_symbols() == ["AAPL"]

    def test_remove(self):
        repo = make_repo()
        repo.add("AAPL")
        repo.remove("AAPL")
        assert repo.list_symbols() == []

    def test_removing_a_symbol_not_present_is_a_no_op(self):
        repo = make_repo()
        repo.remove("AAPL")
        assert repo.list_symbols() == []
