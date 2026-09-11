# Spec: Resiliency of the Stock Data Provider

## Problem

`yfinance` is an unofficial, unauthenticated scrape of Yahoo Finance. It is slow, rate-limited,
and occasionally down. The screener must never let a provider hiccup turn into a 500, a hung
request, or a silently wrong answer.

## Design

Resiliency is applied in exactly one place: `infrastructure/resilient_provider.py`, which
decorates the raw `YFinanceProvider` behind the same `StockDataProvider` port the application
layer depends on. The application layer is unaware resiliency exists — it just sees a
`StockDataProvider` that may return stale data or exclude symbols.

## Policies

| Concern    | Policy                                                                    |
|------------|----------------------------------------------------------------------------|
| Timeout    | 3s per underlying call.                                                   |
| Retry      | 3 attempts, exponential backoff (0.5s base), only on transient errors (timeout, connection error) — never retried on a data-shape error. |
| Circuit breaker | Opens after 5 consecutive provider failures; half-opens after 30s cooldown; one trial call decides close/re-open. Breaker state is per-provider, not per-symbol. |
| Cache      | TTL cache keyed by symbol. Fresh window: 60s. Data older than fresh but younger than 1 hour may be served as a stale fallback. Older than that: symbol is excluded. |

## Degradation ladder (per symbol, in order)

1. Fresh data (within 60s) → served normally, `is_stale=false`.
2. Provider call fails or breaker is open, but cache has data < 1h old → served with
   `is_stale=true`, symbol added to `stale_symbols`.
3. Provider call fails and no usable cache → symbol dropped from results, added to
   `excluded_symbols`.

A batch screen never fails wholesale because of (2) or (3) for a subset of symbols — the
request always returns `200` with whatever could be resolved, plus visibility into what
couldn't.

## Explicit non-goals

No distributed cache, no persistence of quote history, no alerting/paging. This is a
single-process in-memory cache and breaker, adequate for a portfolio-demo deployment.
