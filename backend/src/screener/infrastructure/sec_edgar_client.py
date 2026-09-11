from __future__ import annotations

from datetime import datetime

import httpx

from screener.domain.entities import FilingLink

_REQUEST_TIMEOUT_SECONDS = 5
_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{document}"

# Which form types we surface, and how many of each (latest only). SEC
# EDGAR uses "10-K", "10-Q", "DEF 14A" verbatim as the `form` value.
_WANTED_FORMS = ("10-K", "10-Q", "DEF 14A")

# SEC requires a descriptive User-Agent identifying the requester —
# unauthenticated requests without one are rejected.
_USER_AGENT = "stock-screener (revathi.muppala@example.com)"


def _extract_latest_filings(cik: int, submissions_json: dict) -> list[FilingLink]:
    """Pure parsing of the `submissions/CIK##########.json` shape into the
    latest filing of each wanted form type. Split out from the HTTP-fetching
    client so the tricky bit — picking the latest of each type and building
    a resolvable Archives URL — is unit-testable without a network call."""

    recent = submissions_json.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_documents = recent.get("primaryDocument", [])

    latest_by_form: dict[str, FilingLink] = {}
    for form, filed_date_str, accession_number, document in zip(
        forms, filing_dates, accession_numbers, primary_documents
    ):
        if form not in _WANTED_FORMS or form in latest_by_form:
            continue  # `recent` arrays are already ordered newest-first
        latest_by_form[form] = FilingLink(
            form_type=form,
            filed_date=datetime.strptime(filed_date_str, "%Y-%m-%d").date(),
            url=_ARCHIVE_URL.format(
                cik=cik,
                accession_no_dashes=accession_number.replace("-", ""),
                document=document,
            ),
        )

    return [latest_by_form[form] for form in _WANTED_FORMS if form in latest_by_form]


class SecEdgarClient:
    """Adapter over the public SEC EDGAR API (no auth required). Ticker→CIK
    mapping is fetched once and cached in memory for the process lifetime —
    it's a ~700KB static-ish file, not worth re-fetching per symbol. A
    missing/unmapped ticker or a fetch failure just means "no filings
    found" — never a hard failure for the rest of the company-detail
    response, since this is supplementary data."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=_REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": _USER_AGENT}
        )
        self._cik_by_symbol: dict[str, int] | None = None

    def _load_cik_map(self) -> dict[str, int]:
        if self._cik_by_symbol is not None:
            return self._cik_by_symbol
        try:
            response = self._client.get(_TICKERS_URL)
            response.raise_for_status()
            data = response.json()
        except Exception:
            self._cik_by_symbol = {}
            return self._cik_by_symbol

        self._cik_by_symbol = {
            entry["ticker"].upper(): int(entry["cik_str"]) for entry in data.values()
        }
        return self._cik_by_symbol

    def get_filing_links(self, symbol: str) -> list[FilingLink]:
        cik = self._load_cik_map().get(symbol.upper())
        if cik is None:
            return []

        try:
            response = self._client.get(_SUBMISSIONS_URL.format(cik=cik))
            response.raise_for_status()
            submissions_json = response.json()
        except Exception:
            return []

        return _extract_latest_filings(cik, submissions_json)
