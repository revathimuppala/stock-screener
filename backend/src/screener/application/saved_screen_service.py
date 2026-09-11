from __future__ import annotations

import uuid
from datetime import datetime, timezone

from screener.application.ports import SavedScreenRepository
from screener.domain.entities import SavedScreen, ScreeningCriteria


class SavedScreenService:
    """Use case: save/list/get/delete screens for later re-use. Depends
    only on the SavedScreenRepository port (DIP)."""

    def __init__(self, repository: SavedScreenRepository):
        self._repository = repository

    def save(
        self,
        name: str,
        criteria: ScreeningCriteria | None = None,
        query: str | None = None,
    ) -> SavedScreen:
        if (criteria is None) == (query is None):
            raise ValueError("Exactly one of criteria or query must be provided")
        screen = SavedScreen(
            id=str(uuid.uuid4()),
            name=name,
            criteria=criteria,
            query=query,
            created_at=datetime.now(timezone.utc),
        )
        self._repository.save(screen)
        return screen

    def list(self) -> list[SavedScreen]:
        return self._repository.list()

    def get(self, screen_id: str) -> SavedScreen | None:
        return self._repository.get(screen_id)

    def delete(self, screen_id: str) -> None:
        self._repository.delete(screen_id)
