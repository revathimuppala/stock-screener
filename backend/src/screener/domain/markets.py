"""The selectable screening universes: the fixed MVP default, plus four real
market indices. Deliberately a single active universe at a time (not a merged
superset) — see specs/markets.md. Every market other than "default" is large
enough (100-500+ symbols) that screening it always goes through the async job
path (application/screen_job_service.py), never the synchronous screen/query
endpoints that "default" still uses."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Market:
    id: str
    label: str


DEFAULT_MARKET_ID = "default"

MARKETS: list[Market] = [
    Market(id=DEFAULT_MARKET_ID, label="US Large Cap (Default)"),
    Market(id="sp500", label="S&P 500"),
    Market(id="nasdaq100", label="NASDAQ-100"),
    Market(id="nse500", label="NIFTY 500 (NSE)"),
    Market(id="bse500", label="S&P BSE 500"),
]

_MARKETS_BY_ID = {m.id: m for m in MARKETS}


def is_known_market(market_id: str) -> bool:
    return market_id in _MARKETS_BY_ID
