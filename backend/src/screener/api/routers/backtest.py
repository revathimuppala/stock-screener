import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse

from screener.api.dependencies import get_backtest_job_store, get_backtest_service
from screener.api.schemas import BacktestRequest, BacktestStartResponse
from screener.application.backtest_service import BacktestService
from screener.application.matcher_factory import build_matcher
from screener.domain.dsl.errors import DslError
from screener.domain.entities import ScreeningCriteria
from screener.domain.matcher import Matcher
from screener.infrastructure.backtest_job_store import BacktestJobStore

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])


def _run_job(
    job_id: str,
    matcher: Matcher,
    request: BacktestRequest,
    job_store: BacktestJobStore,
    backtest_service: BacktestService,
) -> None:
    job_store.write(job_id, {"status": "running"})
    try:
        result = backtest_service.run(
            matcher=matcher,
            start=request.start_date,
            end=request.end_date,
            holding_period_days=request.holding_period_days,
            universe_override=request.symbols,
        )
        job_store.write(job_id, asdict(result))
    except Exception as exc:  # a failed job should be visible via polling, not a dropped task
        job_store.write(job_id, {"status": "failed", "error": str(exc)})


@router.post("", status_code=202, response_model=BacktestStartResponse)
def start_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    job_store: BacktestJobStore = Depends(get_backtest_job_store),
    backtest_service: BacktestService = Depends(get_backtest_service),
) -> BacktestStartResponse:
    criteria = ScreeningCriteria(**request.criteria.model_dump()) if request.criteria else None
    try:
        matcher = build_matcher(criteria, request.query)
    except DslError as exc:
        raise HTTPException(
            status_code=400, detail={"error": exc.message, "position": exc.position}
        ) from exc

    job_id = str(uuid.uuid4())
    job_store.write(
        job_id,
        {
            "status": "pending",
            "criteria": request.criteria.model_dump() if request.criteria else None,
            "query": request.query,
            "start_date": str(request.start_date),
            "end_date": str(request.end_date),
            "holding_period_days": request.holding_period_days,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    background_tasks.add_task(_run_job, job_id, matcher, request, job_store, backtest_service)
    return BacktestStartResponse(backtest_id=job_id, status="pending")


@router.get("/{backtest_id}")
def get_backtest(
    backtest_id: str, job_store: BacktestJobStore = Depends(get_backtest_job_store)
) -> JSONResponse:
    record = job_store.read(backtest_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Backtest job not found")
    return JSONResponse(content=record)
