from datetime import datetime, timezone

from screener.domain.entities import SavedScreen, ScreeningCriteria
from screener.infrastructure.sqlite_saved_screen_repository import SqliteSavedScreenRepository


def make_repo() -> SqliteSavedScreenRepository:
    return SqliteSavedScreenRepository(database_url="sqlite:///:memory:")


def make_screen(**overrides) -> SavedScreen:
    defaults = dict(
        id="abc-123",
        name="Cheap tech",
        criteria=ScreeningCriteria(pe_max=20, sector="Technology"),
        query=None,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return SavedScreen(**defaults)


class TestSqliteSavedScreenRepository:
    def test_starts_empty(self):
        repo = make_repo()
        assert repo.list() == []

    def test_save_then_get_round_trips_criteria(self):
        repo = make_repo()
        screen = make_screen()

        repo.save(screen)

        assert repo.get("abc-123") == screen

    def test_save_then_get_round_trips_query(self):
        repo = make_repo()
        screen = make_screen(criteria=None, query='pe < 20 AND sector = "Technology"')

        repo.save(screen)

        assert repo.get("abc-123") == screen

    def test_get_missing_returns_none(self):
        repo = make_repo()
        assert repo.get("missing") is None

    def test_list_returns_all_saved_screens(self):
        repo = make_repo()
        repo.save(make_screen(id="a", name="A"))
        repo.save(make_screen(id="b", name="B"))

        ids = {s.id for s in repo.list()}
        assert ids == {"a", "b"}

    def test_delete(self):
        repo = make_repo()
        repo.save(make_screen())

        repo.delete("abc-123")

        assert repo.get("abc-123") is None

    def test_save_overwrites_existing_id(self):
        repo = make_repo()
        repo.save(make_screen(name="Original"))
        repo.save(make_screen(name="Renamed"))

        assert repo.get("abc-123").name == "Renamed"
        assert len(repo.list()) == 1
