import pytest

from screener.domain.dsl.ast import And, Comparison, Not, Or
from screener.domain.dsl.errors import DslError
from screener.domain.dsl.parser import parse


class TestParserBasics:
    def test_single_comparison(self):
        assert parse("pe < 20") == Comparison(field="pe_ratio", op="<", value=20.0)

    def test_string_comparison(self):
        assert parse('sector = "Technology"') == Comparison(field="sector", op="=", value="Technology")

    def test_pe_alias_resolves_to_pe_ratio(self):
        parsed = parse("pe > 10")
        assert parsed.field == "pe_ratio"


class TestParserPrecedence:
    def test_and_binds_tighter_than_or(self):
        parsed = parse("roe > 1 OR pe < 2 AND price > 3")
        assert parsed == Or(
            Comparison("roe", ">", 1.0),
            And(Comparison("pe_ratio", "<", 2.0), Comparison("price", ">", 3.0)),
        )

    def test_not_binds_tighter_than_and(self):
        parsed = parse("NOT pe < 1 AND price > 2")
        assert parsed == And(Not(Comparison("pe_ratio", "<", 1.0)), Comparison("price", ">", 2.0))

    def test_parens_override_precedence(self):
        parsed = parse("(roe > 1 OR pe < 2) AND price > 3")
        assert parsed == And(
            Or(Comparison("roe", ">", 1.0), Comparison("pe_ratio", "<", 2.0)),
            Comparison("price", ">", 3.0),
        )


class TestParserErrors:
    def test_unknown_field_is_rejected(self):
        with pytest.raises(DslError, match="unknown field"):
            parse("not_a_real_field < 20")

    def test_ordering_operator_on_string_field_is_rejected(self):
        with pytest.raises(DslError, match="not valid for field"):
            parse('sector < "Technology"')

    def test_numeric_field_given_a_string_literal_is_rejected(self):
        with pytest.raises(DslError):
            parse('pe < "twenty"')

    def test_string_field_given_a_number_is_rejected(self):
        with pytest.raises(DslError):
            parse("sector = 5")

    def test_empty_query_is_rejected(self):
        with pytest.raises(DslError, match="empty"):
            parse("")

    def test_trailing_garbage_is_rejected(self):
        with pytest.raises(DslError):
            parse("pe < 20 extra")

    def test_unclosed_paren_is_rejected(self):
        with pytest.raises(DslError):
            parse("(pe < 20")
