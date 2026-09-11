from __future__ import annotations

import math

# Same import-order requirement as the other yfinance adapters: yfinance
# (via pandas/numpy) must load before curl_cffi for curl_cffi's compiled
# extension to dlopen successfully on macOS.
import yfinance as yf
from curl_cffi import requests as cc_requests

from screener.domain.entities import InstitutionalHolder, QuarterlyFinancials, RawFinancials, ShareholdingPattern
from screener.infrastructure.exceptions import TransientProviderError

_REQUEST_TIMEOUT_SECONDS = 10
_MAX_QUARTERS = 6


def _cell(df, row: str, col) -> float | None:
    """Reads one (row, col) cell from a yfinance statement DataFrame,
    tolerating a missing row, a missing column, or NaN — all common when a
    company doesn't report a given line item."""
    if df is None or row not in df.index or col not in df.columns:
        return None
    value = df.loc[row, col]
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return float(value)


class YFinanceFinancialsProvider:
    """Raw adapter over yfinance's balance sheet, quarterly income
    statement, quarterly cash flow, and holders data. No retry/breaker/cache
    here — ResilientFinancialsProvider wraps this, same pattern as
    YFinanceProvider/YFinancePriceHistoryProvider."""

    def __init__(self) -> None:
        self._session = cc_requests.Session(impersonate="chrome", timeout=_REQUEST_TIMEOUT_SECONDS)

    def get_financials(self, symbol: str) -> RawFinancials:
        try:
            ticker = yf.Ticker(symbol, session=self._session)
            balance_sheet = ticker.get_balance_sheet()
            quarterly_income = ticker.get_income_stmt(freq="quarterly")
            quarterly_cashflow = ticker.get_cashflow(freq="quarterly")
            major_holders = ticker.get_major_holders()
            institutional_holders = ticker.get_institutional_holders()
        except Exception as exc:  # yfinance raises a mix of HTTP/parsing errors
            raise TransientProviderError(f"failed to fetch financials for {symbol}") from exc

        total_debt = _cell(balance_sheet, "TotalDebt", balance_sheet.columns[0]) if not balance_sheet.empty else None
        total_assets = (
            _cell(balance_sheet, "TotalAssets", balance_sheet.columns[0]) if not balance_sheet.empty else None
        )

        quarters: list[QuarterlyFinancials] = []
        for col in list(quarterly_income.columns)[:_MAX_QUARTERS]:
            quarters.append(
                QuarterlyFinancials(
                    period_end=col.date(),
                    revenue=_cell(quarterly_income, "TotalRevenue", col),
                    ebit=_cell(quarterly_income, "EBIT", col),
                    ebitda=_cell(quarterly_income, "EBITDA", col),
                    net_income=_cell(quarterly_income, "NetIncome", col),
                    diluted_eps=_cell(quarterly_income, "DilutedEPS", col),
                    operating_cash_flow=_cell(quarterly_cashflow, "OperatingCashFlow", col),
                    free_cash_flow=_cell(quarterly_cashflow, "FreeCashFlow", col),
                )
            )

        shareholding = _parse_shareholding(major_holders, institutional_holders)

        return RawFinancials(
            symbol=symbol,
            total_debt=total_debt,
            total_assets=total_assets,
            quarters=quarters,
            shareholding=shareholding,
        )


def _parse_shareholding(major_holders, institutional_holders) -> ShareholdingPattern | None:
    if major_holders is None or major_holders.empty:
        return None

    def _major(key: str) -> float | None:
        if key not in major_holders.index:
            return None
        value = major_holders.loc[key].iloc[0]
        return float(value) if value is not None and not (isinstance(value, float) and math.isnan(value)) else None

    top_holders: list[InstitutionalHolder] = []
    if institutional_holders is not None and not institutional_holders.empty:
        for _, row in institutional_holders.head(5).iterrows():
            top_holders.append(
                InstitutionalHolder(
                    name=str(row.get("Holder", "Unknown")),
                    value=float(row["Value"]) if row.get("Value") is not None else None,
                    pct_change=float(row["pctChange"]) if row.get("pctChange") is not None else None,
                )
            )

    return ShareholdingPattern(
        insiders_pct=_major("insidersPercentHeld"),
        institutions_pct=_major("institutionsPercentHeld"),
        top_holders=top_holders,
    )
