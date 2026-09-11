from __future__ import annotations

from screener.domain.dsl.ast import And, Comparison, Expression, Not, Or
from screener.domain.entities import Stock

_OPS = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "=": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def evaluate(expression: Expression, stock: Stock) -> bool:
    if isinstance(expression, Comparison):
        return _evaluate_comparison(expression, stock)
    if isinstance(expression, And):
        return evaluate(expression.left, stock) and evaluate(expression.right, stock)
    if isinstance(expression, Or):
        return evaluate(expression.left, stock) or evaluate(expression.right, stock)
    if isinstance(expression, Not):
        return not evaluate(expression.operand, stock)
    raise TypeError(f"unknown DSL expression node: {expression!r}")  # pragma: no cover


def _evaluate_comparison(comparison: Comparison, stock: Stock) -> bool:
    actual = getattr(stock, comparison.field, None)
    if actual is None:
        # SQL-NULL-like: an unknown/missing value never satisfies any
        # comparison, including !=, rather than raising a TypeError.
        return False

    value = comparison.value
    if isinstance(actual, str) and isinstance(value, str):
        actual, value = actual.casefold(), value.casefold()

    return _OPS[comparison.op](actual, value)
