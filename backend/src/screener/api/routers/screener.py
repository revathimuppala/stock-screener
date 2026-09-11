import csv
import io
import uuid
from dataclasses import asdict, fields, replace
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from screener.api.dependencies import (
    get_market_constituents_provider,
    get_screen_job_store,
    get_screening_service,
)
from screener.api.schemas import (
    DslFieldResponse,
    DslFieldsResponse,
    QueryRequest,
    ScreenJobRequest,
    ScreenJobStartResponse,
    ScreenRequest,
    ScreenResponse,
    StockResponse,
)
from screener.application.ports import MarketConstituentsProvider
from screener.application.screening_service import ScreeningService
from screener.domain.dsl.errors import DslError
from screener.domain.dsl.fields import FIELD_ALIASES, FIELD_TYPES
from screener.domain.dsl.matcher import DslMatcher
from screener.domain.entities import ScreeningCriteria, Stock
from screener.domain.markets import is_known_market
from screener.infrastructure.backtest_job_store import BacktestJobStore

router = APIRouter(prefix="/api/v1", tags=["screener"])

# industry/business_summary are internal fields used only by
# CompanyDetailService's competitor lookup — not screening metrics, so
# they're excluded from both this export and StockResponse.
_EXCLUDED_CSV_FIELDS = {"as_of", "industry", "business_summary"}
_CSV_FIELDS = [f.name for f in fields(Stock) if f.name not in _EXCLUDED_CSV_FIELDS]


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

    result = service.screen_with_matcher(matcher, universe_override=request.symbols)
    return ScreenResponse(
        status=result.status,
        results=[StockResponse(**asdict(s)) for s in result.results],
        stale_symbols=result.stale_symbols,
        excluded_symbols=result.excluded_symbols,
        as_of=result.as_of,
    )


@router.get("/screener/fields", response_model=DslFieldsResponse)
def list_dsl_fields() -> DslFieldsResponse:
    """The DSL's field allowlist, for the frontend's query autocomplete —
    generated from fields.py so the suggestions can never drift from what
    the parser actually accepts."""
    return DslFieldsResponse(
        fields=[
            DslFieldResponse(name=name, type="string" if field_type is str else "number")
            for name, field_type in FIELD_TYPES.items()
        ],
        aliases=FIELD_ALIASES,
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


def _resolve_universe(
    request: ScreenJobRequest, market_provider: MarketConstituentsProvider
) -> list[str]:
    """An explicit symbol list still wins over the selected market — same
    precedence the synchronous /screener and /screener/query endpoints
    already give ScreeningCriteria.symbols/QueryRequest.symbols."""
    if request.symbols:
        return request.symbols
    return market_provider.get_symbols(request.market_id)


def _run_screen_job(
    job_id: str,
    request: ScreenJobRequest,
    job_store: BacktestJobStore,
    service: ScreeningService,
    market_provider: MarketConstituentsProvider,
) -> None:
    job_store.write(job_id, {"status": "running"})
    try:
        universe = _resolve_universe(request, market_provider)
        if request.criteria is not None:
            criteria = replace(ScreeningCriteria(**request.criteria.model_dump()), symbols=universe)
            result = service.screen(criteria)
        else:
            assert request.query is not None
            result = service.screen_with_matcher(DslMatcher(request.query), universe_override=universe)
        # ScreeningResult.status ("ok"/"degraded", data-quality) and this
        # job's lifecycle status ("pending"/"running"/"completed"/"failed")
        # are different concepts that happen to share a field name — keep
        # them distinct rather than letting asdict(result)'s "status" silently
        # clobber the job's completion status.
        result_fields = asdict(result)
        screen_status = result_fields.pop("status")
        job_store.write(job_id, {"status": "completed", "screen_status": screen_status, **result_fields})
    except Exception as exc:  # a failed job should be visible via polling, not a dropped task
        job_store.write(job_id, {"status": "failed", "error": str(exc)})


@router.post("/screener/jobs", status_code=202, response_model=ScreenJobStartResponse)
def start_screen_job(
    request: ScreenJobRequest,
    background_tasks: BackgroundTasks,
    job_store: BacktestJobStore = Depends(get_screen_job_store),
    service: ScreeningService = Depends(get_screening_service),
    market_provider: MarketConstituentsProvider = Depends(get_market_constituents_provider),
) -> ScreenJobStartResponse:
    """Async counterpart to /screener and /screener/query, for markets too
    large to screen within one HTTP request (S&P 500, NASDAQ-100, NSE500,
    BSE500 — see domain/markets.py). Mirrors the backtest job pattern
    exactly: BackgroundTasks + a JSON-blob-per-uuid job store, polled via
    GET /screener/jobs/{id}."""
    if not is_known_market(request.market_id):
        raise HTTPException(status_code=400, detail=f"unknown market_id {request.market_id!r}")

    if request.query is not None:
        try:
            DslMatcher(request.query)  # validate eagerly, same as /screener/query
        except DslError as exc:
            raise HTTPException(
                status_code=400, detail={"error": exc.message, "position": exc.position}
            ) from exc

    job_id = str(uuid.uuid4())
    job_store.write(
        job_id,
        {
            "status": "pending",
            "market_id": request.market_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    background_tasks.add_task(_run_screen_job, job_id, request, job_store, service, market_provider)
    return ScreenJobStartResponse(screen_id=job_id, status="pending")


@router.get("/screener/jobs/{screen_id}")
def get_screen_job(
    screen_id: str, job_store: BacktestJobStore = Depends(get_screen_job_store)
) -> JSONResponse:
    record = job_store.read(screen_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Screen job not found")
    return JSONResponse(content=record)
