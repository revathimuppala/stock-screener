from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from screener.domain.dsl.errors import DslError


class TokenType(Enum):
    FIELD = auto()
    NUMBER = auto()
    STRING = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    OP = auto()
    EOF = auto()


@dataclass(frozen=True, slots=True)
class Token:
    type: TokenType
    value: str
    position: int


_KEYWORDS = {"and": TokenType.AND, "or": TokenType.OR, "not": TokenType.NOT}
# Longest-match-first: "<=" must be checked before "<", etc.
_OPERATORS = ("<=", ">=", "!=", "<", ">", "=")


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    n = len(text)

    while i < n:
        c = text[i]

        if c.isspace():
            i += 1
            continue

        if c == "(":
            tokens.append(Token(TokenType.LPAREN, "(", i))
            i += 1
            continue

        if c == ")":
            tokens.append(Token(TokenType.RPAREN, ")", i))
            i += 1
            continue

        if c == '"':
            start = i
            i += 1
            buf: list[str] = []
            while i < n and text[i] != '"':
                buf.append(text[i])
                i += 1
            if i >= n:
                raise DslError("unterminated string literal", start)
            i += 1  # consume closing quote
            tokens.append(Token(TokenType.STRING, "".join(buf), start))
            continue

        matched_op = next((op for op in _OPERATORS if text.startswith(op, i)), None)
        if matched_op:
            tokens.append(Token(TokenType.OP, matched_op, i))
            i += len(matched_op)
            continue

        if c.isdigit() or (c == "-" and i + 1 < n and text[i + 1].isdigit()):
            start = i
            if c == "-":
                i += 1
            while i < n and (text[i].isdigit() or text[i] == "."):
                i += 1
            tokens.append(Token(TokenType.NUMBER, text[start:i], start))
            continue

        if c.isalpha() or c == "_":
            start = i
            while i < n and (text[i].isalnum() or text[i] == "_"):
                i += 1
            word = text[start:i]
            keyword = _KEYWORDS.get(word.lower())
            tokens.append(Token(keyword, word, start) if keyword else Token(TokenType.FIELD, word, start))
            continue

        raise DslError(f"unexpected character {c!r}", i)

    tokens.append(Token(TokenType.EOF, "", n))
    return tokens
