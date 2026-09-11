from __future__ import annotations

from datetime import datetime, timedelta, timezone

import yfinance as yf
from curl_cffi import requests as cc_requests

_REQUEST_TIMEOUT_SECONDS = 5
_CACHE_TTL = timedelta(hours=1)
_TREASURY_TICKER = "^TNX"  # CBOE 10-Year Treasury Note Yield Index


class TreasuryYieldProvider:
    """Fetches the current 10-year Treasury yield as a practical stand-in
    for the AAA corporate bond yield Graham's formula calls for — a single
    shared value, not per-symbol, so a simple cache-with-fallback is enough
    (no need for the per-key ResilientFetcher machinery). If a refresh
    fails, keeps serving the last known value rather than going stale to
    None — a market-wide yield doesn't move enough in an hour for that to
    matter, and it's a strictly better fallback than breaking every Graham
    Value calculation."""

    def __init__(self) -> None:
        self._session = cc_requests.Session(impersonate="chrome", timeout=_REQUEST_TIMEOUT_SECONDS)
        self._cached_yield: float | None = None
        self._cached_at: datetime | None = None

    def get_yield(self) -> float | None:
        now = datetime.now(timezone.utc)
        if self._cached_at is not None and now - self._cached_at < _CACHE_TTL:
            return self._cached_yield

        try:
            info = yf.Ticker(_TREASURY_TICKER, session=self._session).get_info()
            price = info.get("regularMarketPrice")
            if price is not None:
                self._cached_yield = float(price) / 100  # ^TNX quotes yield in percentage points
                self._cached_at = now
        except Exception:
            pass  # keep serving the last known value

        return self._cached_yield
