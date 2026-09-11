import pytest

from screener.domain.valuation import graham_value, simple_dcf_value


class TestGrahamValue:
    def test_known_formula_result(self):
        # V = EPS x (8.5 + 2g) x 4.4 / Y ; g=10% growth, Y=4.4% yield
        # V = 5 x (8.5 + 20) x 4.4 / 4.4 = 5 x 28.5 x 1 = 142.5
        value = graham_value(eps=5.0, growth_rate=0.10, y=0.044)
        assert value == pytest.approx(142.5)

    def test_higher_growth_gives_higher_value(self):
        low = graham_value(eps=5.0, growth_rate=0.05, y=0.044)
        high = graham_value(eps=5.0, growth_rate=0.20, y=0.044)
        assert high > low

    def test_higher_yield_denominator_gives_lower_value(self):
        low_y = graham_value(eps=5.0, growth_rate=0.10, y=0.03)
        high_y = graham_value(eps=5.0, growth_rate=0.10, y=0.08)
        assert high_y < low_y

    def test_none_for_non_positive_eps(self):
        assert graham_value(eps=0.0, growth_rate=0.10, y=0.044) is None
        assert graham_value(eps=-2.0, growth_rate=0.10, y=0.044) is None

    def test_none_for_missing_or_non_positive_yield(self):
        assert graham_value(eps=5.0, growth_rate=0.10, y=None) is None
        assert graham_value(eps=5.0, growth_rate=0.10, y=0.0) is None

    def test_missing_growth_rate_defaults_to_zero_growth(self):
        value = graham_value(eps=5.0, growth_rate=None, y=0.044)
        # V = 5 x (8.5 + 0) x 4.4 / 4.4 = 5 x 8.5 = 42.5
        assert value == pytest.approx(42.5)

    def test_very_negative_growth_does_not_produce_a_negative_value(self):
        value = graham_value(eps=5.0, growth_rate=-0.50, y=0.044)
        assert value >= 0


class TestSimpleDcfValue:
    def test_returns_a_positive_value_for_healthy_inputs(self):
        value = simple_dcf_value(
            fcf=1_000_000_000, growth_rate=0.08, shares_outstanding=100_000_000
        )
        assert value is not None
        assert value > 0

    def test_higher_growth_gives_higher_value(self):
        low = simple_dcf_value(fcf=1_000_000_000, growth_rate=0.02, shares_outstanding=100_000_000)
        high = simple_dcf_value(fcf=1_000_000_000, growth_rate=0.20, shares_outstanding=100_000_000)
        assert high > low

    def test_none_for_non_positive_fcf(self):
        assert simple_dcf_value(fcf=0.0, growth_rate=0.08, shares_outstanding=100) is None
        assert simple_dcf_value(fcf=-5.0, growth_rate=0.08, shares_outstanding=100) is None

    def test_none_for_missing_or_non_positive_shares_outstanding(self):
        assert simple_dcf_value(fcf=1000.0, growth_rate=0.08, shares_outstanding=None) is None
        assert simple_dcf_value(fcf=1000.0, growth_rate=0.08, shares_outstanding=0) is None

    def test_extreme_growth_rate_is_clamped_not_left_to_explode(self):
        clamped = simple_dcf_value(fcf=1_000_000_000, growth_rate=5.0, shares_outstanding=100_000_000)
        normal_high = simple_dcf_value(
            fcf=1_000_000_000, growth_rate=0.25, shares_outstanding=100_000_000
        )
        assert clamped == pytest.approx(normal_high)

    def test_missing_growth_rate_defaults_to_zero_growth(self):
        value = simple_dcf_value(fcf=1_000_000_000, growth_rate=None, shares_outstanding=100_000_000)
        assert value is not None
        assert value > 0
