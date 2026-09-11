import pytest

from screener.domain.dsl.errors import DslError
from screener.domain.dsl.tokens import TokenType, tokenize


class TestTokenizer:
    def test_tokenizes_a_full_expression(self):
        tokens = tokenize('pe < 20 AND sector = "Technology"')
        types = [t.type for t in tokens]
        values = [t.value for t in tokens]

        assert types == [
            TokenType.FIELD,
            TokenType.OP,
            TokenType.NUMBER,
            TokenType.AND,
            TokenType.FIELD,
            TokenType.OP,
            TokenType.STRING,
            TokenType.EOF,
        ]
        assert values[0] == "pe"
        assert values[2] == "20"
        assert values[6] == "Technology"

    def test_two_char_operators_are_not_split(self):
        tokens = tokenize("pe <= 20")
        assert tokens[1].type == TokenType.OP
        assert tokens[1].value == "<="

    def test_negative_numbers(self):
        tokens = tokenize("earnings_growth > -0.5")
        assert tokens[2].type == TokenType.NUMBER
        assert tokens[2].value == "-0.5"

    def test_parens(self):
        tokens = tokenize("(pe < 20)")
        assert [t.type for t in tokens[:3]] == [TokenType.LPAREN, TokenType.FIELD, TokenType.OP]

    def test_keywords_are_case_insensitive(self):
        tokens = tokenize("pe < 20 and sector = \"Technology\" or not pe > 5")
        types = [t.type for t in tokens]
        assert TokenType.AND in types
        assert TokenType.OR in types
        assert TokenType.NOT in types

    def test_unterminated_string_raises_with_position(self):
        with pytest.raises(DslError) as exc_info:
            tokenize('sector = "Technology')
        assert exc_info.value.position == 9

    def test_unexpected_character_raises_with_position(self):
        with pytest.raises(DslError) as exc_info:
            tokenize("pe @ 20")
        assert exc_info.value.position == 3
