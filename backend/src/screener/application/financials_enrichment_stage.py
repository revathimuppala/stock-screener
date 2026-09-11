from __future__ import annotations

from dataclasses import replace

from screener.application.ports import FinancialsProvider
from screener.domain.entities import Stock


class FinancialsEnrichmentStage:
    """Attaches debt_to_assets and cfo_to_operating_profit to every stock
    in a result set — deliberately separate from YFinanceProvider.fetch()
    (which only reads the quote `info` dict) since these need the balance
    sheet and quarterly statements, a heavier, separately-cached fetch.
    Same "enrich the final result set" shape as TechnicalFilterStage."""

    def __init__(self, financials_provider: FinancialsProvider):
        self._financials_provider = financials_provider

    def enrich(self, stocks: list[Stock]) -> list[Stock]:
        enriched = []
        for stock in stocks:
            financials = self._financials_provider.get_financials(stock.symbol)
            if financials is None:
                enriched.append(stock)
                continue

            debt_to_assets = None
            if financials.total_debt is not None and financials.total_assets:
                debt_to_assets = financials.total_debt / financials.total_assets

            cfo_to_operating_profit = None
            if financials.quarters:
                latest = financials.quarters[0]
                if latest.operating_cash_flow is not None and latest.ebit:
                    cfo_to_operating_profit = latest.operating_cash_flow / latest.ebit

            enriched.append(
                replace(
                    stock,
                    debt_to_assets=debt_to_assets,
                    cfo_to_operating_profit=cfo_to_operating_profit,
                )
            )
        return enriched
