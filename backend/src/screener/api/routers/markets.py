from fastapi import APIRouter

from screener.api.schemas import MarketResponse, MarketsResponse
from screener.domain.markets import MARKETS

router = APIRouter(prefix="/api/v1", tags=["markets"])


@router.get("/markets", response_model=MarketsResponse)
def list_markets() -> MarketsResponse:
    """The selectable screening universes — generated from domain/markets.py
    so the frontend dropdown can never drift from what's actually
    supported (same single-source-of-truth pattern as /screener/fields)."""
    return MarketsResponse(markets=[MarketResponse(id=m.id, label=m.label) for m in MARKETS])
