# FinTech Stock Screener & Portfolio Dashboard (MVP)

A stock screener over a fixed large-cap universe, built to demonstrate a production-credible
Python + Next.js full-stack workflow: spec-driven development, TDD, BDD, Clean Code/SOLID
architecture, and explicit resiliency around a flaky third-party data source (`yfinance`).

## Scope

- **In scope**: stock screening (P/E, market cap, sector, dividend-yield filters) and a
  watchlist, both built on one resilient data-access stack.
- **Deferred (Phase 2)**: portfolio tracking (holdings, P&L, allocation), auth, real-time
  streaming, historical charting.

See `backend/specs/screener.md` and `backend/specs/resiliency.md` for the full specs, and
`backend/features/*.feature` for the BDD scenarios that drove the implementation.

## Architecture

```
backend/src/screener/
  domain/          # entities, value objects, filter strategies — no framework deps
  application/      # use-case services + Protocol "ports" — depends on domain only
  infrastructure/    # yfinance adapter, resiliency wrapper, cache, SQLite repo
  api/              # FastAPI routers, DI wiring, pydantic schemas
```

`domain` never imports from the other layers; `application` defines the `StockDataProvider`
and `WatchlistRepository` ports; `infrastructure` implements them; `api` wires everything
together in one composition root (`api/dependencies.py`). A new screening filter is a new
class implementing `ScreeningFilter` — no existing code changes (OCP). Resiliency (timeout,
retry, circuit breaker, stale-cache fallback) lives entirely in
`infrastructure/resilient_provider.py`, wrapping the raw `YFinanceProvider` — the application
layer only ever sees the `StockDataProvider` port.

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
make e2e             # playwright: end-to-end screener flow
```
