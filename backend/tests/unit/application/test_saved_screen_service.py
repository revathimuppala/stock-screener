import pytest

from screener.application.saved_screen_service import SavedScreenService
from screener.domain.entities import ScreeningCriteria


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


class TestSavedScreenServiceCriteria:
    def test_saving_a_criteria_screen_makes_it_listable(self):
        service = SavedScreenService(repository=InMemorySavedScreenRepository())

        saved = service.save(name="Cheap tech", criteria=ScreeningCriteria(pe_max=20))

        assert [s.id for s in service.list()] == [saved.id]
        assert service.list()[0].name == "Cheap tech"
        assert service.list()[0].criteria == ScreeningCriteria(pe_max=20)
        assert service.list()[0].query is None

    def test_get_by_id(self):
        service = SavedScreenService(repository=InMemorySavedScreenRepository())
        saved = service.save(name="Cheap tech", criteria=ScreeningCriteria(pe_max=20))

        assert service.get(saved.id) == saved

    def test_get_missing_id_returns_none(self):
        service = SavedScreenService(repository=InMemorySavedScreenRepository())
        assert service.get("missing") is None

    def test_delete(self):
        service = SavedScreenService(repository=InMemorySavedScreenRepository())
        saved = service.save(name="Cheap tech", criteria=ScreeningCriteria(pe_max=20))

        service.delete(saved.id)

        assert service.list() == []


class TestSavedScreenServiceQuery:
    def test_saving_a_dsl_query_screen(self):
        service = SavedScreenService(repository=InMemorySavedScreenRepository())

        saved = service.save(name="High yield tech", query='pe < 20 AND sector = "Technology"')

        assert saved.query == 'pe < 20 AND sector = "Technology"'
        assert saved.criteria is None


class TestSavedScreenServiceValidation:
    def test_requires_exactly_one_of_criteria_or_query(self):
        service = SavedScreenService(repository=InMemorySavedScreenRepository())

        with pytest.raises(ValueError):
            service.save(name="Bad", criteria=None, query=None)

    def test_rejects_both_criteria_and_query(self):
        service = SavedScreenService(repository=InMemorySavedScreenRepository())

        with pytest.raises(ValueError):
            service.save(name="Bad", criteria=ScreeningCriteria(), query="pe < 20")
