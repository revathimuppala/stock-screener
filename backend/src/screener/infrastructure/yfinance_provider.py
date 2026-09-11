from __future__ import annotations

from datetime import datetime, timezone

# Import order matters here: yfinance's own import chain (via pandas/numpy)
# loads CoreFoundation on macOS before curl_cffi's compiled extension does,
# which is what lets curl_cffi's dlopen succeed in this process. Importing
# curl_cffi before yfinance (or standalone) fails to load on macOS.
import yfinance as yf
from curl_cffi import requests as cc_requests

from screener.domain.entities import Stock
from screener.infrastructure.exceptions import ProviderDataError, TransientProviderError

_REQUEST_TIMEOUT_SECONDS = 3


class YFinanceProvider:
    """Raw adapter over yfinance. Implements SingleSymbolFetcher only — no
    retry, no breaker, no cache. Those concerns live one layer up in
    ResilientStockDataProvider, which is what the application actually
    depends on.

    yfinance now requires Yahoo requests to go through a curl_cffi session
    with browser impersonation (a plain requests.Session is rejected) — we
    build that session ourselves so we can still enforce our own timeout
    budget rather than trusting yfinance's default."""

    def __init__(self) -> None:
        self._session = cc_requests.Session(impersonate="chrome", timeout=_REQUEST_TIMEOUT_SECONDS)

    def fetch(self, symbol: str) -> Stock:
        try:
            info = yf.Ticker(symbol, session=self._session).get_info()
        except cc_requests.RequestsError as exc:
            raise TransientProviderError(f"timed out fetching {symbol}") from exc
        except Exception as exc:  # yfinance raises a mix of HTTP/parsing errors
            raise TransientProviderError(f"failed to fetch {symbol}") from exc

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        name = info.get("longName") or info.get("shortName")
        if price is None or name is None:
            raise ProviderDataError(f"incomplete data for {symbol}")

        return Stock(
            symbol=symbol,
            name=name,
            sector=info.get("sector") or "Unknown",
            price=float(price),
            pe_ratio=_as_float(info.get("trailingPE")),
            market_cap=_as_float(info.get("marketCap")),
            dividend_yield=_dividend_yield(info, float(price)),
            as_of=datetime.now(timezone.utc),
            is_stale=False,
        )


def _as_float(value: object) -> float | None:
    return float(value) if value is not None else None


def _dividend_yield(info: dict, price: float) -> float | None:
    """`info["dividendYield"]` is unreliable — Yahoo sometimes returns it as
    a raw percent (e.g. 0.34 meaning 0.34%) rather than a fraction, which
    would silently read as a 34% yield. `trailingAnnualDividendYield` is
    consistently a proper fraction; fall back to rate/price if it's absent."""
    trailing = info.get("trailingAnnualDividendYield")
    if trailing is not None:
        return float(trailing)
    rate = info.get("dividendRate")
    if rate is not None and price:
        return float(rate) / price
    return None
