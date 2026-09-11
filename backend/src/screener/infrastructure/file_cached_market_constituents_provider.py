from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from screener.application.ports import MarketConstituentsProvider

_DEFAULT_TTL = timedelta(hours=24)


class FileCachedMarketConstituentsProvider:
    """Wraps a raw MarketConstituentsProvider with a long-TTL, per-market
    JSON cache at `data_dir/<market_id>.json` — index membership changes
    rarely (semiannual rebalancing is typical), so there's no reason to hit
    GitHub/Wikipedia/NSE/bseindices on every screen, and BSE500's build
    involves ~500 extra Yahoo-search round trips that are far too slow to
    repeat per request. On a fetch failure, serves the last-known cached
    list rather than failing the whole screen (same resilience philosophy
    as TreasuryYieldProvider) — only propagates the error if there's truly
    nothing cached yet."""

    def __init__(self, inner: MarketConstituentsProvider, data_dir: Path, ttl: timedelta = _DEFAULT_TTL):
        self._inner = inner
        self._data_dir = data_dir
        self._ttl = ttl

    def get_symbols(self, market_id: str) -> list[str]:
        path = self._path(market_id)
        cached = self._read(path)

        if cached is not None and self._is_fresh(cached):
            return cached["symbols"]

        try:
            symbols = self._inner.get_symbols(market_id)
        except Exception:
            if cached is not None:
                return cached["symbols"]
            raise

        self._write(path, symbols)
        return symbols

    def _path(self, market_id: str) -> Path:
        return self._data_dir / f"{market_id}.json"

    def _read(self, path: Path) -> dict | None:
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def _is_fresh(self, cached: dict) -> bool:
        fetched_at = datetime.fromisoformat(cached["fetched_at"])
        return datetime.now(timezone.utc) - fetched_at < self._ttl

    def _write(self, path: Path, symbols: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"symbols": symbols, "fetched_at": datetime.now(timezone.utc).isoformat()}
        path.write_text(json.dumps(record))
