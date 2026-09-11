from screener.infrastructure.market_constituents_provider import (
    _parse_bse500_names,
    _parse_nasdaq100_wikitext,
    _parse_nse500_csv,
    _parse_sp500_csv,
)

_SP500_SAMPLE = """Symbol,Security,GICS Sector,GICS Sub-Industry,Headquarters Location,Date added,CIK,Founded
MMM,3M,Industrials,Industrial Conglomerates,"Saint Paul, Minnesota",1957-03-04,66740,1902
BRK.B,Berkshire Hathaway,Financials,Multi-Sector Holdings,"Omaha, Nebraska",2010-02-16,1067983,1839
BF.B,Brown-Forman,Consumer Staples,Distillers & Vintners,"Louisville, Kentucky",1982-10-31,14693,1870
"""

_NASDAQ100_SAMPLE = """{| class="wikitable sortable" id="constituents"
|-
! Ticker !! Company !! ICB Industry !! ICB Subsector
|-
| ADBE || [[Adobe Inc.]] || Technology || Software
|-
| GOOGL || [[Alphabet Inc.]] (Class A) || Technology || Software
|-
| GOOG || [[Alphabet Inc.]] (Class C) || Technology || Software
|}
==References==
"""

_NSE500_SAMPLE = """Company Name,Industry,Symbol,Series,ISIN Code
360 ONE WAM Ltd.,Financial Services,360ONE,EQ,INE466L01038
3M India Ltd.,Diversified,3MINDIA,EQ,INE470A01017
ABB India Ltd.,Capital Goods,ABB,EQ,INE117A01022
"""

_BSE500_SAMPLE = {
    "Table": [
        {"SCRIP_CODE": "500002", "SCRIPNAME": "ABB INDIA LIMITED", "Industry_name": "Industrials"},
        {"SCRIP_CODE": "539254", "SCRIPNAME": "Adani Energy Solutions Limited", "Industry_name": "Utilities"},
    ]
}


class TestParseSp500Csv:
    def test_extracts_symbols(self):
        assert _parse_sp500_csv(_SP500_SAMPLE) == ["MMM", "BRK-B", "BF-B"]

    def test_converts_dot_share_classes_to_dash_for_yfinance(self):
        symbols = _parse_sp500_csv(_SP500_SAMPLE)
        assert "BRK-B" in symbols
        assert "BRK.B" not in symbols


class TestParseNasdaq100Wikitext:
    def test_extracts_tickers_from_table_rows(self):
        assert _parse_nasdaq100_wikitext(_NASDAQ100_SAMPLE) == ["ADBE", "GOOGL", "GOOG"]

    def test_ignores_the_header_row(self):
        assert "Ticker" not in _parse_nasdaq100_wikitext(_NASDAQ100_SAMPLE)


class TestParseNse500Csv:
    def test_extracts_symbols_with_ns_suffix(self):
        assert _parse_nse500_csv(_NSE500_SAMPLE) == ["360ONE.NS", "3MINDIA.NS", "ABB.NS"]


class TestParseBse500Names:
    def test_extracts_company_names(self):
        assert _parse_bse500_names(_BSE500_SAMPLE) == [
            "ABB INDIA LIMITED",
            "Adani Energy Solutions Limited",
        ]

    def test_handles_empty_table(self):
        assert _parse_bse500_names({"Table": []}) == []
