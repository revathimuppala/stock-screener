# Spec: Stock Screener

## Problem

A user wants to filter a universe of stocks by fundamental criteria (valuation, size, sector,
income) and get back a ranked list, without needing to know anything about the underlying data
provider or its reliability characteristics.

## Universe

The MVP screens a fixed universe of 30 large-cap US equities spanning multiple sectors
(Technology, Financials, Healthcare, Consumer, Energy, Industrials). The universe is a static
list in `domain/universe.py`. Expanding it later is a data change, not a code change.

## Criteria (all optional; omitted criteria impose no constraint)

| Field               | Type          | Meaning                                    |
|---------------------|---------------|---------------------------------------------|
| `pe_min` / `pe_max` | float         | Price/Earnings ratio range (inclusive)     |
| `market_cap_min/max`| float (USD)   | Market capitalization range (inclusive)    |
| `sector`            | string        | Exact sector match                         |
| `min_dividend_yield`| float (0-1)   | Minimum trailing dividend yield            |

A stock must satisfy **all** provided criteria (AND semantics) to appear in results.

## Ranking

Results are ranked by dividend yield descending, then by P/E ascending (cheaper first) as a
tiebreaker. This is a simple, explainable default — not a scoring model.

## Response contract

- `status`: `"ok"` when every requested symbol was served from fresh data; `"degraded"` when
  any symbol was served from stale cache or excluded due to provider failure.
- `results`: the ranked, filtered stock list. Each entry carries `is_stale` so the UI can flag
  individual rows; any `is_stale=true` entry implies the overall batch `status` is `"degraded"`.
- `stale_symbols`: symbols present in `results` but served from cache past the fresh TTL.
- `excluded_symbols`: symbols that could not be evaluated at all (no fresh data, no cache) and
  are therefore absent from `results`. An empty screen (no matches) is a valid `200` with an
  empty `results` array — it is not an error.

## Out of scope for this spec (see specs/resiliency.md)

How the data is fetched, retried, cached, or degraded — that is a resiliency concern, not a
screening concern, and lives in the infrastructure layer.
