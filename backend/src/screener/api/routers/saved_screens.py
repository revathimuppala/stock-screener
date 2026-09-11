from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from screener.api.dependencies import get_saved_screen_service, get_screening_service
from screener.api.schemas import (
    SavedScreenListResponse,
    SavedScreenResponse,
    SaveScreenRequest,
    ScreenRequest,
    ScreenResponse,
    StockResponse,
)
from screener.application.matcher_factory import build_matcher
from screener.application.saved_screen_service import SavedScreenService
from screener.application.screening_service import ScreeningService
from screener.domain.dsl.errors import DslError
from screener.domain.entities import SavedScreen, ScreeningCriteria

router = APIRouter(prefix="/api/v1/screens", tags=["saved-screens"])


def _to_response(screen: SavedScreen) -> SavedScreenResponse:
    return SavedScreenResponse(
        id=screen.id,
        name=screen.name,
        criteria=ScreenRequest(**asdict(screen.criteria)) if screen.criteria else None,
        query=screen.query,
        created_at=screen.created_at,
    )


@router.get("", response_model=SavedScreenListResponse)
def list_screens(service: SavedScreenService = Depends(get_saved_screen_service)) -> SavedScreenListResponse:
    return SavedScreenListResponse(screens=[_to_response(s) for s in service.list()])


@router.post("", response_model=SavedScreenResponse, status_code=201)
def save_screen(
    request: SaveScreenRequest,
    service: SavedScreenService = Depends(get_saved_screen_service),
) -> SavedScreenResponse:
    criteria = ScreeningCriteria(**request.criteria.model_dump()) if request.criteria else None
    if request.query is not None:
        try:
            build_matcher(None, request.query)  # validate it parses before ever saving it
        except DslError as exc:
            raise HTTPException(status_code=422, detail=f"Invalid query: {exc.message}") from exc
    saved = service.save(name=request.name, criteria=criteria, query=request.query)
    return _to_response(saved)


@router.delete("/{screen_id}", status_code=204)
def delete_screen(screen_id: str, service: SavedScreenService = Depends(get_saved_screen_service)) -> None:
    service.delete(screen_id)


@router.get("/{screen_id}/run", response_model=ScreenResponse)
def run_screen(
    screen_id: str,
    saved_screens: SavedScreenService = Depends(get_saved_screen_service),
    screening_service: ScreeningService = Depends(get_screening_service),
) -> ScreenResponse:
    screen = saved_screens.get(screen_id)
    if screen is None:
        raise HTTPException(status_code=404, detail="Saved screen not found")

    matcher = build_matcher(screen.criteria, screen.query)
    result = screening_service.screen_with_matcher(matcher)
    return ScreenResponse(
        status=result.status,
        results=[StockResponse(**asdict(s)) for s in result.results],
        stale_symbols=result.stale_symbols,
        excluded_symbols=result.excluded_symbols,
        as_of=result.as_of,
    )
