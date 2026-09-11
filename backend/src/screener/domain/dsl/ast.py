from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True, slots=True)
class Comparison:
    """A leaf condition: FIELD OP literal. Plain data — no behavior — so
    the AST shape is testable independently of evaluation, and so a saved
    query can later be pretty-printed or "explained" without a refactor."""

    field: str
    op: str
    value: float | str


@dataclass(frozen=True, slots=True)
class And:
    left: "Expression"
    right: "Expression"


@dataclass(frozen=True, slots=True)
class Or:
    left: "Expression"
    right: "Expression"


@dataclass(frozen=True, slots=True)
class Not:
    operand: "Expression"


Expression = Union[Comparison, And, Or, Not]
