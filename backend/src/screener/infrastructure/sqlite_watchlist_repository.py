from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table, create_engine, delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

_metadata = MetaData()

_watchlist_table = Table(
    "watchlist",
    _metadata,
    Column("symbol", String, primary_key=True),
)


class SqliteWatchlistRepository:
    """SQLite-backed WatchlistRepository. An in-memory URL uses a
    StaticPool so the schema and data survive across calls within one
    repository instance (SQLAlchemy otherwise opens a fresh, empty
    in-memory database per connection)."""

    def __init__(self, database_url: str = "sqlite:///watchlist.db"):
        is_memory = ":memory:" in database_url
        self._engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool if is_memory else None,
        )
        _metadata.create_all(self._engine)

    def add(self, symbol: str) -> None:
        with self._engine.begin() as conn:
            try:
                conn.execute(insert(_watchlist_table).values(symbol=symbol))
            except IntegrityError:
                pass  # already present — add is idempotent

    def remove(self, symbol: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(_watchlist_table).where(_watchlist_table.c.symbol == symbol))

    def list_symbols(self) -> list[str]:
        with self._engine.connect() as conn:
            rows = conn.execute(select(_watchlist_table.c.symbol).order_by(_watchlist_table.c.symbol))
            return [row.symbol for row in rows]
