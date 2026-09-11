from dataclasses import asdict

from fastapi import APIRouter, Depends

from screener.api.dependencies import get_screening_service
from screener.api.schemas import ScreenRequest, ScreenResponse, StockResponse
from screener.application.screening_service import ScreeningService
from screener.domain.entities import ScreeningCriteria

router = APIRouter(prefix="/api/v1", tags=["screener"])


@router.post("/screener", response_model=ScreenResponse)
def screen_stocks(
    request: ScreenRequest,
    service: ScreeningService = Depends(get_screening_service),
) -> ScreenResponse:
    criteria = ScreeningCriteria(**request.model_dump())
    result = service.screen(criteria)
    return ScreenResponse(
        status=result.status,
        results=[StockResponse(**asdict(s)) for s in result.results],
        stale_symbols=result.stale_symbols,
        excluded_symbols=result.excluded_symbols,
        as_of=result.as_of,
    )
