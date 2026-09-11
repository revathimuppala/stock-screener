"""The fixed MVP screening universe: large-cap US equities across sectors.
Expanding this is a data change, not a code change — see specs/screener.md."""

# Grouping comments below are informal; the ground truth for each symbol's
# `sector` is whatever yfinance reports (a GICS-like taxonomy — e.g.
# "Financial Services" and "Consumer Cyclical"/"Consumer Defensive", not
# "Financials"/"Consumer"). The frontend's sector filter options
# (frontend/components/screener/FilterForm.tsx) must match those real values.
UNIVERSE: list[str] = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "NVDA", "AVGO", "ORCL", "CRM",
    # Financial Services
    "JPM", "BAC", "GS", "MA", "V",
    # Healthcare
    "UNH", "JNJ", "LLY", "PFE", "ABBV",
    # Consumer Cyclical / Consumer Defensive
    "AMZN", "WMT", "PG", "KO", "MCD", "NKE",
    # Energy
    "XOM", "CVX", "COP",
    # Industrials
    "CAT", "BA", "HON", "UPS",
    # Utilities / Communication Services
    "NEE", "VZ",
]
