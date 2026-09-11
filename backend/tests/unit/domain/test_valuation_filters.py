from datetime import datetime, timezone

from screener.domain.entities import Stock
from screener.domain.filters import (
    CfoToOperatingProfitMinFilter,
    DebtToAssetsMaxFilter,
    EvToEbitdaMaxFilter,
    OperatingMarginMinFilter,
    PegRatioMaxFilter,
)


def make_stock(**overrides) -> Stock:
    defaults = dict(
        symbol="AAPL",
        name="Apple Inc.",
        sector="Technology",
        price=190.0,
        pe_ratio=15.0,
        market_cap=3_000_000_000_000.0,
        dividend_yield=0.005,
        as_of=datetime(2026, 1, 1, tzinfo=timezone.utc),
        is_stale=False,
    )
    defaults.update(overrides)
    return Stock(**defaults)


class TestPegRatioMaxFilter:
    def test_within_max(self):
        assert PegRatioMaxFilter(peg_ratio_max=3.0).matches(make_stock(peg_ratio=2.5)) is True

    def test_above_max(self):
        assert PegRatioMaxFilter(peg_ratio_max=1.0).matches(make_stock(peg_ratio=2.5)) is False

    def test_none_fails(self):
        assert PegRatioMaxFilter(peg_ratio_max=3.0).matches(make_stock(peg_ratio=None)) is False


class TestEvToEbitdaMaxFilter:
    def test_within_max(self):
        assert EvToEbitdaMaxFilter(ev_to_ebitda_max=20.0).matches(make_stock(ev_to_ebitda=15.0)) is True

    def test_above_max(self):
        assert EvToEbitdaMaxFilter(ev_to_ebitda_max=10.0).matches(make_stock(ev_to_ebitda=15.0)) is False


class TestOperatingMarginMinFilter:
    def test_meets_minimum(self):
        f = OperatingMarginMinFilter(operating_margin_min=0.20)
        assert f.matches(make_stock(operating_margin=0.30)) is True

    def test_below_minimum(self):
        f = OperatingMarginMinFilter(operating_margin_min=0.40)
        assert f.matches(make_stock(operating_margin=0.30)) is False


class TestDebtToAssetsMaxFilter:
    def test_within_max(self):
        f = DebtToAssetsMaxFilter(debt_to_assets_max=0.5)
        assert f.matches(make_stock(debt_to_assets=0.3)) is True

    def test_above_max(self):
        f = DebtToAssetsMaxFilter(debt_to_assets_max=0.2)
        assert f.matches(make_stock(debt_to_assets=0.3)) is False


class TestCfoToOperatingProfitMinFilter:
    def test_meets_minimum(self):
        f = CfoToOperatingProfitMinFilter(cfo_to_operating_profit_min=0.8)
        assert f.matches(make_stock(cfo_to_operating_profit=1.1)) is True

    def test_below_minimum(self):
        f = CfoToOperatingProfitMinFilter(cfo_to_operating_profit_min=1.2)
        assert f.matches(make_stock(cfo_to_operating_profit=1.1)) is False
