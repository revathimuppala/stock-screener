from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, MetaData, String, Table, create_engine, delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.pool import StaticPool

from screener.domain.entities import SavedScreen, ScreeningCriteria

_metadata = MetaData()

_saved_screens_table = Table(
    "saved_screens",
    _metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("criteria_json", String, nullable=True),
    Column("query_text", String, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def _row_to_screen(row) -> SavedScreen:
    criteria = ScreeningCriteria(**json.loads(row.criteria_json)) if row.criteria_json else None
    created_at = row.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return SavedScreen(
        id=row.id,
        name=row.name,
        criteria=criteria,
        query=row.query_text,
        created_at=created_at,
    )


class SqliteSavedScreenRepository:
    """SQLite-backed SavedScreenRepository. Mirrors
    SqliteWatchlistRepository's StaticPool-for-in-memory approach."""

    def __init__(self, database_url: str = "sqlite:///saved_screens.db"):
        is_memory = ":memory:" in database_url
        self._engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool if is_memory else None,
        )
        _metadata.create_all(self._engine)

    def save(self, screen: SavedScreen) -> None:
        criteria_json = json.dumps(asdict(screen.criteria)) if screen.criteria is not None else None
        with self._engine.begin() as conn:
            stmt = sqlite_insert(_saved_screens_table).values(
                id=screen.id,
                name=screen.name,
                criteria_json=criteria_json,
                query_text=screen.query,
                created_at=screen.created_at,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": stmt.excluded.name,
                    "criteria_json": stmt.excluded.criteria_json,
                    "query_text": stmt.excluded.query_text,
                    "created_at": stmt.excluded.created_at,
                },
            )
            conn.execute(stmt)

    def list(self) -> list[SavedScreen]:
        with self._engine.connect() as conn:
            rows = conn.execute(select(_saved_screens_table).order_by(_saved_screens_table.c.created_at))
            return [_row_to_screen(row) for row in rows]

    def get(self, screen_id: str) -> SavedScreen | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(_saved_screens_table).where(_saved_screens_table.c.id == screen_id)
            ).first()
            return _row_to_screen(row) if row else None

    def delete(self, screen_id: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(_saved_screens_table).where(_saved_screens_table.c.id == screen_id))
