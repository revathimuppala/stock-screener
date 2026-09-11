from __future__ import annotations

import csv
import io
import logging
import re
import time

import httpx

from screener.infrastructure.exceptions import ProviderDataError

logger = logging.getLogger(__name__)

# A plain httpx client without a browser User-Agent gets rejected/served a
# JS-only shell by some of these sources (verified live for bseindices.com;
# NSE's archive worked either way but we set it everywhere for consistency).
_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_SP500_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
# The rendered Wikipedia page loses the table structure — `action=raw` gets
# the actual wikitext, verified live.
_NASDAQ100_URL = "https://en.wikipedia.org/w/index.php?title=List_of_NASDAQ-100_companies&action=raw"
_NSE500_URL = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
# code=17 is "BSE 500" — verified against the full index list at
# .../api/AsiaIndexList/w. Don't confuse with code=149 ("BSE India 150", a
# different, smaller index that happens to look similar at a glance.
_BSE500_URL = "https://www.bseindices.com/AsiaIndexAPI/api/Codewise_Indices/w?code=17"
_YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"

# BSE's API only gives a company name + BSE's own numeric scrip code, and
# that numeric code does NOT work as a yfinance ticker (verified live:
# 500002.BO / 532321.BO both resolve to nothing) — yfinance's .BO convention
# is the alphabetic trading symbol, same style as NSE. So each BSE500 name
# needs one extra round trip through Yahoo's own search endpoint to find its
# real symbol. This paces those ~500 extra calls rather than firing them in
# a burst.
_YAHOO_SEARCH_PACING_SECONDS = 0.05


def _parse_sp500_csv(csv_text: str) -> list[str]:
    reader = csv.DictReader(io.StringIO(csv_text))
    # Share classes are "BRK.B" in this CSV but yfinance wants "BRK-B".
    return [row["Symbol"].strip().replace(".", "-") for row in reader if row.get("Symbol")]


# Matches wikitext table data rows shaped like "| ADBE || [[Adobe Inc.]] ...".
# The header row uses "!" not "|" so it's never matched.
_NASDAQ100_ROW_RE = re.compile(r"^\| ([A-Z]{1,5}) \|\|", re.MULTILINE)


def _parse_nasdaq100_wikitext(text: str) -> list[str]:
    return _NASDAQ100_ROW_RE.findall(text)


def _parse_nse500_csv(csv_text: str) -> list[str]:
    reader = csv.DictReader(io.StringIO(csv_text))
    return [f"{row['Symbol'].strip()}.NS" for row in reader if row.get("Symbol")]


def _parse_bse500_names(data: dict) -> list[str]:
    return [row["SCRIPNAME"] for row in data.get("Table", []) if row.get("SCRIPNAME")]


class LiveMarketConstituentsProvider:
    """Raw adapter fetching each market's constituent list from its real
    live source. No caching/resiliency of its own —
    FileCachedMarketConstituentsProvider wraps this the same way
    FileCachedPriceHistoryProvider wraps the raw yfinance price adapter."""

    def __init__(self, timeout_seconds: float = 10) -> None:
        self._client = httpx.Client(
            timeout=timeout_seconds, headers={"User-Agent": _BROWSER_USER_AGENT}
        )

    def get_symbols(self, market_id: str) -> list[str]:
        if market_id == "sp500":
            return self._fetch_sp500()
        if market_id == "nasdaq100":
            return self._fetch_nasdaq100()
        if market_id == "nse500":
            return self._fetch_nse500()
        if market_id == "bse500":
            return self._fetch_bse500()
        raise ProviderDataError(f"unknown market_id {market_id!r}")

    def _fetch_sp500(self) -> list[str]:
        response = self._client.get(_SP500_URL)
        response.raise_for_status()
        return _parse_sp500_csv(response.text)

    def _fetch_nasdaq100(self) -> list[str]:
        response = self._client.get(_NASDAQ100_URL)
        response.raise_for_status()
        return _parse_nasdaq100_wikitext(response.text)

    def _fetch_nse500(self) -> list[str]:
        response = self._client.get(_NSE500_URL)
        response.raise_for_status()
        return _parse_nse500_csv(response.text)

    def _fetch_bse500(self) -> list[str]:
        response = self._client.get(_BSE500_URL)
        response.raise_for_status()
        names = _parse_bse500_names(response.json())

        symbols: list[str] = []
        for name in names:
            symbol = self._resolve_bo_symbol(name)
            if symbol is None:
                logger.warning("could not resolve a BSE .BO symbol for %r", name)
            else:
                symbols.append(symbol)
            time.sleep(_YAHOO_SEARCH_PACING_SECONDS)

        # Yahoo's fuzzy search occasionally cross-matches two distinct
        # company names to the same symbol (observed live: one such
        # collision out of ~500 names) — dedup while preserving order.
        return list(dict.fromkeys(symbols))

    def _resolve_bo_symbol(self, company_name: str) -> str | None:
        try:
            response = self._client.get(
                _YAHOO_SEARCH_URL,
                params={"q": company_name, "quotesCount": 5, "newsCount": 0},
            )
            response.raise_for_status()
            data = response.json()
        except Exception:
            return None

        for quote in data.get("quotes", []):
            if quote.get("exchange") == "BSE":
                symbol = quote.get("symbol")
                if isinstance(symbol, str):
                    return symbol
        return None
