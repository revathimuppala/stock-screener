from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from screener.api.dependencies import get_company_detail_service
from screener.api.schemas import CompanyDetailResponse
from screener.application.company_detail_service import CompanyDetailService

router = APIRouter(prefix="/api/v1", tags=["companies"])


@router.get("/companies/{symbol}", response_model=CompanyDetailResponse)
def get_company_detail(
    symbol: str,
    service: CompanyDetailService = Depends(get_company_detail_service),
) -> CompanyDetailResponse:
    detail = service.get_detail(symbol.upper())
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No data available for {symbol.upper()}")
    return CompanyDetailResponse(**asdict(detail))
