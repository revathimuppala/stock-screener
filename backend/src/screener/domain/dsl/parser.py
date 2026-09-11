from __future__ import annotations

from screener.domain.dsl.ast import And, Comparison, Expression, Not, Or
from screener.domain.dsl.errors import DslError
from screener.domain.dsl.fields import FIELD_TYPES, resolve_field
from screener.domain.dsl.tokens import Token, TokenType, tokenize

_NUMERIC_ONLY_OPS = {"<", "<=", ">", ">="}


class _Parser:
    """Recursive-descent parser for:
    expr := or_expr
    or_expr := and_expr ("OR" and_expr)*
    and_expr := unary ("AND" unary)*
    unary := "NOT" unary | atom
    atom := comparison | "(" expr ")"
    comparison := FIELD OP literal
    """

    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._pos = 0

    def parse(self) -> Expression:
        expr = self._or_expr()
        self._expect(TokenType.EOF)
        return expr

    def _or_expr(self) -> Expression:
        left = self._and_expr()
        while self._peek().type == TokenType.OR:
            self._advance()
            left = Or(left, self._and_expr())
        return left

    def _and_expr(self) -> Expression:
        left = self._unary()
        while self._peek().type == TokenType.AND:
            self._advance()
            left = And(left, self._unary())
        return left

    def _unary(self) -> Expression:
        if self._peek().type == TokenType.NOT:
            self._advance()
            return Not(self._unary())
        return self._atom()

    def _atom(self) -> Expression:
        if self._peek().type == TokenType.LPAREN:
            self._advance()
            expr = self._or_expr()
            self._expect(TokenType.RPAREN)
            return expr
        return self._comparison()

    def _comparison(self) -> Comparison:
        field_tok = self._expect(TokenType.FIELD)
        canonical = resolve_field(field_tok.value)
        if canonical is None:
            raise DslError(f"unknown field {field_tok.value!r}", field_tok.position)

        op_tok = self._expect(TokenType.OP)
        value_tok = self._advance()
        field_type = FIELD_TYPES[canonical]

        if value_tok.type == TokenType.NUMBER:
            if field_type is not float:
                raise DslError(f"field {canonical!r} is not numeric", value_tok.position)
            value: float | str = float(value_tok.value)
        elif value_tok.type == TokenType.STRING:
            if field_type is not str:
                raise DslError(f"field {canonical!r} is not a string field", value_tok.position)
            value = value_tok.value
        else:
            raise DslError(f"expected a value, got {value_tok.value!r}", value_tok.position)

        if op_tok.value in _NUMERIC_ONLY_OPS and field_type is not float:
            raise DslError(f"operator {op_tok.value!r} is not valid for field {canonical!r}", op_tok.position)

        return Comparison(field=canonical, op=op_tok.value, value=value)

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    def _expect(self, type_: TokenType) -> Token:
        token = self._peek()
        if token.type != type_:
            raise DslError(f"expected {type_.name}, got {token.value!r}", token.position)
        return self._advance()


def parse(text: str) -> Expression:
    if not text.strip():
        raise DslError("empty query", 0)
    return _Parser(tokenize(text)).parse()
