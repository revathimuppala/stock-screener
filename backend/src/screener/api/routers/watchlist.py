from fastapi import APIRouter, Depends, Response

from screener.api.dependencies import get_watchlist_service
from screener.api.schemas import AddWatchlistSymbolRequest, WatchlistResponse
from screener.application.watchlist_service import WatchlistService

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])


@router.get("", response_model=WatchlistResponse)
def list_watchlist(service: WatchlistService = Depends(get_watchlist_service)) -> WatchlistResponse:
    return WatchlistResponse(symbols=service.list_symbols())


@router.post("", response_model=WatchlistResponse, status_code=201)
def add_to_watchlist(
    request: AddWatchlistSymbolRequest,
    service: WatchlistService = Depends(get_watchlist_service),
) -> WatchlistResponse:
    service.add_symbol(request.symbol)
    return WatchlistResponse(symbols=service.list_symbols())


@router.delete("/{symbol}", status_code=204, response_class=Response)
def remove_from_watchlist(
    symbol: str,
    service: WatchlistService = Depends(get_watchlist_service),
) -> Response:
    service.remove_symbol(symbol)
    return Response(status_code=204)
