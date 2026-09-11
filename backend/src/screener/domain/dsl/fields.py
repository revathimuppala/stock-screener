"""The DSL's field allowlist: query field name -> (Stock attribute name,
declared type). Deliberately explicit rather than reflecting over Stock's
dataclass fields — a query can only ever reference what's listed here, by
construction, not by sandboxing.

Deliberately EXCLUDED: sma_50/sma_100/sma_200/rsi_14 (TechnicalFilterStage)
and debt_to_assets/cfo_to_operating_profit (FinancialsEnrichmentStage).
Those are populated by enrichment stages that run *after* matching (see
ScreeningService.screen) — a DSL query is evaluated against the raw quote,
before enrichment, so those fields would always read as None. They're
reachable via the structured criteria form (above_sma_window, rsi_min/max,
debt_to_assets_max, cfo_to_operating_profit_min), which runs its own
enrich-then-filter pass; exposing them in the DSL too would need matching
plumbing, not attempted here."""

FIELD_TYPES: dict[str, type] = {
    "symbol": str,
    "name": str,
    "sector": str,
    "price": float,
    "pe_ratio": float,
    "market_cap": float,
    "dividend_yield": float,
    "roe": float,
    "debt_to_equity": float,
    "price_to_book": float,
    "earnings_growth": float,
    "revenue_growth": float,
    "fifty_two_week_high": float,
    "fifty_two_week_low": float,
    "peg_ratio": float,
    "ev_to_ebitda": float,
    "operating_margin": float,
    "graham_value": float,
    "dcf_value": float,
}

# Shorthands users are likely to type.
FIELD_ALIASES: dict[str, str] = {
    "pe": "pe_ratio",
    "peg": "peg_ratio",
    "ev_ebitda": "ev_to_ebitda",
}


def resolve_field(name: str) -> str | None:
    """Returns the canonical field name, or None if unknown."""
    lowered = name.lower()
    canonical = FIELD_ALIASES.get(lowered, lowered)
    return canonical if canonical in FIELD_TYPES else None
