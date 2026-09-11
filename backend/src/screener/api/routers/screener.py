import csv
import io
from dataclasses import asdict, fields

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from screener.api.dependencies import get_screening_service
from screener.api.schemas import QueryRequest, ScreenRequest, ScreenResponse, StockResponse
from screener.application.screening_service import ScreeningService
from screener.domain.dsl.errors import DslError
from screener.domain.dsl.matcher import DslMatcher
from screener.domain.entities import ScreeningCriteria, Stock

router = APIRouter(prefix="/api/v1", tags=["screener"])

_CSV_FIELDS = [f.name for f in fields(Stock) if f.name != "as_of"]


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


@router.post("/screener/query", response_model=ScreenResponse)
def query_stocks(
    request: QueryRequest,
    service: ScreeningService = Depends(get_screening_service),
) -> ScreenResponse:
    try:
        matcher = DslMatcher(request.query)
    except DslError as exc:
        raise HTTPException(
            status_code=400, detail={"error": exc.message, "position": exc.position}
        ) from exc

    result = service.screen_with_matcher(matcher)
    return ScreenResponse(
        status=result.status,
        results=[StockResponse(**asdict(s)) for s in result.results],
        stale_symbols=result.stale_symbols,
        excluded_symbols=result.excluded_symbols,
        as_of=result.as_of,
    )


@router.get("/screener/export")
def export_screen_csv(
    request: ScreenRequest = Depends(),
    service: ScreeningService = Depends(get_screening_service),
) -> PlainTextResponse:
    criteria = ScreeningCriteria(**request.model_dump())
    result = service.screen(criteria)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_CSV_FIELDS)
    for stock in result.results:
        row = asdict(stock)
        writer.writerow([row[field] for field in _CSV_FIELDS])

    return PlainTextResponse(content=buffer.getvalue(), media_type="text/csv")
