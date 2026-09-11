from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class BacktestJobStore:
    """The job record *is* the file — data/backtesting/<uuid>.json. No
    separate metadata store to keep in sync: create writes {"status":
    "pending", ...}, the background task overwrites the same file as it
    moves through "running" to "completed"/"failed", and reads just return
    whatever's currently on disk."""

    def __init__(self, data_dir: Path):
        self._data_dir = data_dir

    def write(self, job_id: str, record: dict[str, Any]) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._path(job_id).write_text(json.dumps(record, default=str))

    def read(self, job_id: str) -> dict[str, Any] | None:
        path = self._path(job_id)
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def _path(self, job_id: str) -> Path:
        return self._data_dir / f"{job_id}.json"
