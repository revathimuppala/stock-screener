# FinTech Stock Screener & Portfolio Dashboard

A stock screener over a fixed large-cap universe, built to demonstrate a production-credible
Python + Next.js full-stack workflow: spec-driven development, TDD, BDD, Clean Code/SOLID
architecture, and explicit resiliency around a flaky third-party data source (`yfinance`).

## Features

- **Screener**: filter by P/E, market cap, sector, dividend yield, ROE, debt/equity, P/B,
  earnings/revenue growth, 52-week-high proximity, and price-above-N-day-SMA — sortable results.
- **Advanced Query**: a small boolean query language (`pe < 20 AND sector = "Technology" AND
  (roe > 0.15 OR dividend_yield > 0.02)`) as an alternative to the structured filter form.
- **Saved Screens**: save either a structured screen or a query, list/run/delete them later.
- **Watchlist**: track symbols you want to revisit.
- **CSV export** of the current screen's results.
- **Backtesting**: replay a screen (criteria or query) against real historical daily prices —
  async job (submit → poll → results), a match timeline, and per-match simulated performance
  (entry/exit/return) on click. Fundamental fields are frozen at today's values for the whole
  window (yfinance has no historical point-in-time fundamentals) — every result says so.
- **Deferred**: portfolio tracking (holdings, P&L, allocation), auth, real-time streaming,
  alerts, chart-pattern matching.

See `backend/specs/*.md` for the written specs and `backend/features/*.feature` for the BDD
scenarios that drove the implementation.

## Architecture

```
backend/src/screener/
  domain/          # entities, value objects, filter strategies, DSL parser/evaluator — no
                     framework deps
  application/      # use-case services + Protocol "ports" — depends on domain only
  infrastructure/    # yfinance adapters, resiliency wrapper, file/SQLite caches & repos
  api/              # FastAPI routers, DI wiring, pydantic schemas
```

`domain` never imports from the other layers. `application` defines the ports
(`StockDataProvider`, `PriceHistoryProvider`, `WatchlistRepository`, `SavedScreenRepository`);
`infrastructure` implements them; `api` wires everything together in one composition root
(`api/dependencies.py`). A new screening filter is a new class implementing `ScreeningFilter` —
no existing code changes (OCP). The structured filter form and the query language both produce
a `Matcher` (`domain/matcher.py`), so `ScreeningService` and `BacktestService` don't care which
one built it.

**Resiliency** (timeout, retry, circuit breaker, stale-cache fallback) lives in
`infrastructure/resilience.py` (`ResilientFetcher`), shared by both the live-quote provider and
the price-history provider — the application layer only ever sees the port, never the resiliency
mechanics. Historical prices and derived analytics (moving averages) are cached to disk under
`backend/data/` (`returns/<SYMBOL>/returns.csv`, `analytics/<SYMBOL>/<yyyymmdd>.csv`,
`backtesting/<uuid>.json`) — gitignored, regenerated on demand.

## Running it

```bash
make backend-install    # poetry install
make frontend-install   # npm install
make dev                # runs FastAPI (:8000) + Next.js (:3000) together
```

Or individually: `make backend-dev`, `make frontend-dev`.

## Testing

```bash
make backend-test    # pytest: unit, integration, BDD, API contract — with coverage
make frontend-test   # vitest: component + client tests
make e2e             # playwright: end-to-end flows (screener, query, backtest)
```
