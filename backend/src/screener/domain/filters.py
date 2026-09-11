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
        return cls(filters)

    def matches(self, stock: Stock) -> bool:
        return all(f.matches(stock) for f in self._filters)

    def apply(self, stocks: list[Stock]) -> list[Stock]:
        return [s for s in stocks if self.matches(s)]
