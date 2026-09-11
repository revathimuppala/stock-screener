from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from screener.domain.entities import ScreeningCriteria, Stock


class ScreeningFilter(Protocol):
    """A single screening predicate. New filters implement this — existing
    filters and the service that composes them never need to change (OCP)."""

    def matches(self, stock: Stock) -> bool: ...


@dataclass(frozen=True, slots=True)
class PeRangeFilter:
    pe_min: float | None
    pe_max: float | None

    def matches(self, stock: Stock) -> bool:
        if self.pe_min is None and self.pe_max is None:
            return True
        if stock.pe_ratio is None:
            return False
        if self.pe_min is not None and stock.pe_ratio < self.pe_min:
            return False
        if self.pe_max is not None and stock.pe_ratio > self.pe_max:
            return False
        return True


@dataclass(frozen=True, slots=True)
class MarketCapFilter:
    market_cap_min: float | None
    market_cap_max: float | None

    def matches(self, stock: Stock) -> bool:
        if self.market_cap_min is None and self.market_cap_max is None:
            return True
        if stock.market_cap is None:
            return False
        if self.market_cap_min is not None and stock.market_cap < self.market_cap_min:
            return False
        if self.market_cap_max is not None and stock.market_cap > self.market_cap_max:
            return False
        return True


@dataclass(frozen=True, slots=True)
class SectorFilter:
    sector: str

    def matches(self, stock: Stock) -> bool:
        return stock.sector.casefold() == self.sector.casefold()


@dataclass(frozen=True, slots=True)
class DividendYieldFilter:
    min_dividend_yield: float

    def matches(self, stock: Stock) -> bool:
        if stock.dividend_yield is None:
            return False
        return stock.dividend_yield >= self.min_dividend_yield


@dataclass(frozen=True, slots=True)
class RoeMinFilter:
    roe_min: float

    def matches(self, stock: Stock) -> bool:
        if stock.roe is None:
            return False
        return stock.roe >= self.roe_min


@dataclass(frozen=True, slots=True)
class DebtToEquityMaxFilter:
    debt_to_equity_max: float

    def matches(self, stock: Stock) -> bool:
        if stock.debt_to_equity is None:
            return False
        return stock.debt_to_equity <= self.debt_to_equity_max


@dataclass(frozen=True, slots=True)
class PriceToBookMaxFilter:
    price_to_book_max: float

    def matches(self, stock: Stock) -> bool:
        if stock.price_to_book is None:
            return False
        return stock.price_to_book <= self.price_to_book_max


@dataclass(frozen=True, slots=True)
class EarningsGrowthMinFilter:
    earnings_growth_min: float

    def matches(self, stock: Stock) -> bool:
        if stock.earnings_growth is None:
            return False
        return stock.earnings_growth >= self.earnings_growth_min


@dataclass(frozen=True, slots=True)
class RevenueGrowthMinFilter:
    revenue_growth_min: float

    def matches(self, stock: Stock) -> bool:
        if stock.revenue_growth is None:
            return False
        return stock.revenue_growth >= self.revenue_growth_min


@dataclass(frozen=True, slots=True)
class FiftyTwoWeekProximityFilter:
    """Matches when price is within `within_pct` (a 0-1 fraction) of the
    52-week high."""

    within_pct: float

    def matches(self, stock: Stock) -> bool:
        if stock.fifty_two_week_high is None or stock.fifty_two_week_high <= 0:
            return False
        shortfall = (stock.fifty_two_week_high - stock.price) / stock.fifty_two_week_high
        return shortfall <= self.within_pct


@dataclass(frozen=True, slots=True)
class PegRatioMaxFilter:
    peg_ratio_max: float

    def matches(self, stock: Stock) -> bool:
        if stock.peg_ratio is None:
            return False
        return stock.peg_ratio <= self.peg_ratio_max


@dataclass(frozen=True, slots=True)
class EvToEbitdaMaxFilter:
    ev_to_ebitda_max: float

    def matches(self, stock: Stock) -> bool:
        if stock.ev_to_ebitda is None:
            return False
        return stock.ev_to_ebitda <= self.ev_to_ebitda_max


@dataclass(frozen=True, slots=True)
class OperatingMarginMinFilter:
    operating_margin_min: float

    def matches(self, stock: Stock) -> bool:
        if stock.operating_margin is None:
            return False
        return stock.operating_margin >= self.operating_margin_min


@dataclass(frozen=True, slots=True)
class DebtToAssetsMaxFilter:
    debt_to_assets_max: float

    def matches(self, stock: Stock) -> bool:
        if stock.debt_to_assets is None:
            return False
        return stock.debt_to_assets <= self.debt_to_assets_max


@dataclass(frozen=True, slots=True)
class CfoToOperatingProfitMinFilter:
    cfo_to_operating_profit_min: float

    def matches(self, stock: Stock) -> bool:
        if stock.cfo_to_operating_profit is None:
            return False
        return stock.cfo_to_operating_profit >= self.cfo_to_operating_profit_min


@dataclass(frozen=True, slots=True)
class RsiRangeFilter:
    rsi_min: float | None
    rsi_max: float | None

    def matches(self, stock: Stock) -> bool:
        if stock.rsi_14 is None:
            return False
        if self.rsi_min is not None and stock.rsi_14 < self.rsi_min:
            return False
        if self.rsi_max is not None and stock.rsi_14 > self.rsi_max:
            return False
        return True


class FilterChain:
    """Combines filters built from ScreeningCriteria with AND semantics."""

    def __init__(self, filters: list[ScreeningFilter]):
        self._filters = filters

    @classmethod
    def from_criteria(cls, criteria: ScreeningCriteria) -> "FilterChain":
        filters: list[ScreeningFilter] = []
        if criteria.pe_min is not None or criteria.pe_max is not None:
            filters.append(PeRangeFilter(criteria.pe_min, criteria.pe_max))
        if criteria.market_cap_min is not None or criteria.market_cap_max is not None:
            filters.append(MarketCapFilter(criteria.market_cap_min, criteria.market_cap_max))
        if criteria.sector is not None:
            filters.append(SectorFilter(criteria.sector))
        if criteria.min_dividend_yield is not None:
            filters.append(DividendYieldFilter(criteria.min_dividend_yield))
        if criteria.roe_min is not None:
            filters.append(RoeMinFilter(criteria.roe_min))
        if criteria.debt_to_equity_max is not None:
            filters.append(DebtToEquityMaxFilter(criteria.debt_to_equity_max))
        if criteria.price_to_book_max is not None:
            filters.append(PriceToBookMaxFilter(criteria.price_to_book_max))
        if criteria.earnings_growth_min is not None:
            filters.append(EarningsGrowthMinFilter(criteria.earnings_growth_min))
        if criteria.revenue_growth_min is not None:
            filters.append(RevenueGrowthMinFilter(criteria.revenue_growth_min))
        if criteria.near_52_week_high_pct is not None:
            filters.append(FiftyTwoWeekProximityFilter(criteria.near_52_week_high_pct))
        if criteria.peg_ratio_max is not None:
            filters.append(PegRatioMaxFilter(criteria.peg_ratio_max))
        if criteria.ev_to_ebitda_max is not None:
            filters.append(EvToEbitdaMaxFilter(criteria.ev_to_ebitda_max))
        if criteria.operating_margin_min is not None:
            filters.append(OperatingMarginMinFilter(criteria.operating_margin_min))
        if criteria.debt_to_assets_max is not None:
            filters.append(DebtToAssetsMaxFilter(criteria.debt_to_assets_max))
        if criteria.cfo_to_operating_profit_min is not None:
            filters.append(CfoToOperatingProfitMinFilter(criteria.cfo_to_operating_profit_min))
        # rsi_min/rsi_max and above_sma_window are deliberately NOT added here:
        # they depend on price history fetched by TechnicalAnalysisStage
        # *after* this chain runs (see ScreeningService.screen), not on the
        # raw quote every other filter above reads from.
        return cls(filters)

    def matches(self, stock: Stock) -> bool:
        return all(f.matches(stock) for f in self._filters)

    def apply(self, stocks: list[Stock]) -> list[Stock]:
        return [s for s in stocks if self.matches(s)]
