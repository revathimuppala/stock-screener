from datetime import date

from screener.infrastructure.sec_edgar_client import _extract_latest_filings


def _submissions(forms, filing_dates, accession_numbers, primary_documents):
    return {
        "filings": {
            "recent": {
                "form": forms,
                "filingDate": filing_dates,
                "accessionNumber": accession_numbers,
                "primaryDocument": primary_documents,
            }
        }
    }


class TestExtractLatestFilings:
    def test_picks_the_first_occurrence_of_each_wanted_form(self):
        submissions = _submissions(
            forms=["8-K", "10-Q", "10-Q", "10-K", "DEF 14A"],
            filing_dates=["2026-08-01", "2026-07-15", "2026-04-15", "2026-02-01", "2026-03-01"],
            accession_numbers=[
                "0000320193-26-000090",
                "0000320193-26-000080",
                "0000320193-26-000050",
                "0000320193-26-000010",
                "0000320193-26-000020",
            ],
            primary_documents=["a.htm", "b.htm", "c.htm", "d.htm", "e.htm"],
        )

        result = _extract_latest_filings(320193, submissions)

        assert [f.form_type for f in result] == ["10-K", "10-Q", "DEF 14A"]
        ten_k = next(f for f in result if f.form_type == "10-K")
        assert ten_k.filed_date == date(2026, 2, 1)
        assert ten_k.url == (
            "https://www.sec.gov/Archives/edgar/data/320193/000032019326000010/d.htm"
        )

    def test_ignores_form_types_not_in_the_wanted_list(self):
        submissions = _submissions(
            forms=["8-K", "4"],
            filing_dates=["2026-08-01", "2026-07-01"],
            accession_numbers=["0000320193-26-000090", "0000320193-26-000091"],
            primary_documents=["a.htm", "b.htm"],
        )

        assert _extract_latest_filings(320193, submissions) == []

    def test_missing_recent_filings_returns_empty_list(self):
        assert _extract_latest_filings(320193, {"filings": {}}) == []

    def test_only_returns_forms_that_are_actually_present(self):
        submissions = _submissions(
            forms=["10-K"],
            filing_dates=["2026-02-01"],
            accession_numbers=["0000320193-26-000010"],
            primary_documents=["d.htm"],
        )

        result = _extract_latest_filings(320193, submissions)

        assert [f.form_type for f in result] == ["10-K"]
