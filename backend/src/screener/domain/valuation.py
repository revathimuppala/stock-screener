"""Pure intrinsic-value estimators. No I/O — callers supply already-fetched
numbers, which is what keeps these trivially unit-testable with plain
floats. Both are deliberately simple, documented models, not "the" fair
value — see specs/valuation.md for the assumptions and their limits."""

from __future__ import annotations

_DEFAULT_DISCOUNT_RATE = 0.10
_DEFAULT_TERMINAL_GROWTH = 0.03
_GROWTH_CLAMP = 0.25  # cap wild growth assumptions from distorting the model


def graham_value(eps: float | None, growth_rate: float | None, y: float | None) -> float | None:
    """Benjamin Graham's revised (1974) formula: V = EPS x (8.5 + 2g) x 4.4 / Y,
    where g and Y are expressed in percentage points. `growth_rate` and `y`
    are accepted as fractions (0.10 = 10%) to match every other field in
    this app, and converted internally. Undefined for a loss-making company
    (eps <= 0) or a missing/non-positive yield; a very negative growth
    assumption is floored at 0 rather than producing a negative "value"."""
    if eps is None or eps <= 0:
        return None
    if y is None or y <= 0:
        return None

    g_pct = (growth_rate or 0.0) * 100
    y_pct = y * 100
    growth_multiplier = max(8.5 + 2 * g_pct, 0.0)
    return eps * growth_multiplier * 4.4 / y_pct


def simple_dcf_value(
    fcf: float | None,
    growth_rate: float | None,
    shares_outstanding: float | None,
    discount_rate: float = _DEFAULT_DISCOUNT_RATE,
    terminal_growth: float = _DEFAULT_TERMINAL_GROWTH,
    years: int = 5,
) -> float | None:
    """A simplified DCF: project free cash flow forward `years` at a
    (clamped) growth rate, discount each year back at `discount_rate`, add
    a Gordon-growth terminal value, divide by shares outstanding. Requires
    positive FCF and share count — undefined otherwise (a negative/zero FCF
    company isn't something this simple model can meaningfully value)."""
    if fcf is None or fcf <= 0:
        return None
    if shares_outstanding is None or shares_outstanding <= 0:
        return None

    g = max(min(growth_rate or 0.0, _GROWTH_CLAMP), -_GROWTH_CLAMP)

    present_value = 0.0
    cash_flow = fcf
    for year in range(1, years + 1):
        cash_flow *= 1 + g
        present_value += cash_flow / (1 + discount_rate) ** year

    terminal_value = cash_flow * (1 + terminal_growth) / (discount_rate - terminal_growth)
    present_value += terminal_value / (1 + discount_rate) ** years

    return present_value / shares_outstanding
