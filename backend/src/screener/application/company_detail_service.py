from __future__ import annotations

from screener.application.ports import FilingLinkProvider, FinancialsProvider, StockDataProvider
from screener.domain.entities import CompanyDetail, CompanyProfile
from screener.domain.universe import UNIVERSE

_MAX_COMPETITORS = 5
_ORDER_BACKLOG_NOTE = (
    "Order backlog is not available as structured data from any free source — "
    "see the latest 10-Q for order/bookings disclosures."
)


class CompanyDetailService:
    """Composes financials, filing links, and a business/competitor profile
    for one symbol — the drill-in view from a screener result row. Heavier
    than a screen (SEC filings + full statements + a universe-wide industry
    lookup), so it's only called when a user opens a single symbol, never
    as part of `ScreeningService`."""

    def __init__(
        self,
        stock_data_provider: StockDataProvider,
        financials_provider: FinancialsProvider,
        filing_link_provider: FilingLinkProvider,
    ) -> None:
        self._stock_data_provider = stock_data_provider
        self._financials_provider = financials_provider
        self._filing_link_provider = filing_link_provider

    def get_detail(self, symbol: str) -> CompanyDetail | None:
        symbols_to_fetch = UNIVERSE if symbol in UNIVERSE else [*UNIVERSE, symbol]
        batch = self._stock_data_provider.get_quotes(symbols_to_fetch)
        target = next((s for s in batch.stocks if s.symbol == symbol), None)
        if target is None:
            return None

        competitors = (
            [
                s.symbol
                for s in batch.stocks
                if s.symbol != symbol and s.industry == target.industry
            ][:_MAX_COMPETITORS]
            if target.industry is not None
            else []
        )

        profile = CompanyProfile(
            business_summary=target.business_summary,
            sector=target.sector,
            industry=target.industry,
            competitors=competitors,
            order_backlog_note=_ORDER_BACKLOG_NOTE,
        )

        financials = self._financials_provider.get_financials(symbol)
        filings = self._filing_link_provider.get_filing_links(symbol)

        return CompanyDetail(
            symbol=symbol,
            profile=profile,
            quarters=financials.quarters if financials else [],
            shareholding=financials.shareholding if financials else None,
            filings=filings,
        )
