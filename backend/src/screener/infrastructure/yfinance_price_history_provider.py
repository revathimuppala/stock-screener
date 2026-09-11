from __future__ import annotations

from datetime import date, timedelta

# Same import-order requirement as yfinance_provider.py: yfinance (via
# pandas/numpy) must load before curl_cffi for curl_cffi's compiled
# extension to dlopen successfully on macOS.
import yfinance as yf
from curl_cffi import requests as cc_requests

from screener.domain.entities import PriceBar
from screener.infrastructure.exceptions import TransientProviderError

_REQUEST_TIMEOUT_SECONDS = 5


class YFinancePriceHistoryProvider:
    """Raw adapter over yfinance's historical daily bars. No caching, no
    retry/breaker — FileCachedPriceHistoryProvider wraps this for the
    disk cache, and callers that need retry/breaker compose it the same
    way ResilientStockDataProvider composes YFinanceProvider."""

    def __init__(self) -> None:
        self._session = cc_requests.Session(impersonate="chrome", timeout=_REQUEST_TIMEOUT_SECONDS)

    def get_history(self, symbol: str, start: date, end: date) -> list[PriceBar]:
        try:
            # yfinance's `end` is exclusive; we treat it as inclusive.
            df = yf.Ticker(symbol, session=self._session).history(
                start=start.isoformat(), end=(end + timedelta(days=1)).isoformat()
            )
        except Exception as exc:  # yfinance raises a mix of HTTP/parsing errors
            raise TransientProviderError(f"failed to fetch history for {symbol}") from exc

        return [
            PriceBar(date=timestamp.date(), close=float(row["Close"]))
            for timestamp, row in df.iterrows()
        ]
