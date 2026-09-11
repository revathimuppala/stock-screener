"""The DSL's field allowlist: query field name -> (Stock attribute name,
declared type). Deliberately explicit rather than reflecting over Stock's
dataclass fields — a query can only ever reference what's listed here, by
construction, not by sandboxing."""

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
}

# Shorthands users are likely to type.
FIELD_ALIASES: dict[str, str] = {
    "pe": "pe_ratio",
}


def resolve_field(name: str) -> str | None:
    """Returns the canonical field name, or None if unknown."""
    lowered = name.lower()
    canonical = FIELD_ALIASES.get(lowered, lowered)
    return canonical if canonical in FIELD_TYPES else None
