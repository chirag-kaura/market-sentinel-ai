"""Unit tests for FinancialDocumentParser (Phase 9 — Step 9.1)."""
from datetime import datetime, timezone
import pytest
from intelligence.rag.document_parser import FinancialDocumentParser


@pytest.fixture
def parser():
    return FinancialDocumentParser()


def test_pagination_and_footer_stripping(parser):
    raw_filing = (
        "RELIANCE INDUSTRIES LIMITED\n"
        "CIN: L17110MH1973PLC019786\n"
        "Regd. Office: Maker Chambers IV, 3rd Floor, Nariman Point, Mumbai 400021\n"
        "Outcome of Board Meeting\n"
        "The Board of Directors at its meeting held today has approved an interim dividend.\n"
        "Page 1 of 5\n"
        "Financial Results\n"
        "Revenue from operations stood at Rs 2,45,000 crore for the quarter.\n"
        "- 2 -\n"
    )

    t0 = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
    res = parser.parse_document(
        doc_id="DOC_RIL_001",
        raw_text=raw_filing,
        ticker="RELIANCE",
        company_name="Reliance Industries Limited",
        filing_date=t0
    )

    assert "CIN:" not in res.full_cleaned_text
    assert "Regd. Office:" not in res.full_cleaned_text
    assert "Page 1 of 5" not in res.full_cleaned_text
    assert "- 2 -" not in res.full_cleaned_text
    assert len(res.sections) >= 2


def test_section_boundary_detection(parser):
    raw_filing = (
        "Outcome of Board Meeting\n"
        "The Board approved the demerger of its financial services business.\n"
        "Financial Results\n"
        "Net profit surged by 18% YoY to Rs 18,200 crore.\n"
        "Management Discussion and Analysis\n"
        "Strong consumer demand drove retail performance across grocery and electronics."
    )

    res = parser.parse_document(
        doc_id="DOC_SEC_001",
        raw_text=raw_filing,
        ticker="RELIANCE",
        company_name="Reliance Industries Limited",
        filing_date=datetime.now(timezone.utc)
    )

    section_titles = [s.section_title for s in res.sections]
    assert "Outcome of Board Meeting" in section_titles
    assert "Financial Results" in section_titles
    assert "Management Discussion & Analysis" in section_titles


def test_tabular_statement_detection(parser):
    text_with_table = (
        "Segment Revenue:\n"
        "Retail\t\t50,000\t\t45,000\n"
        "Digital\t\t30,000\t\t25,000\n"
    )
    res = parser.parse_document(
        doc_id="DOC_TAB_001",
        raw_text=text_with_table,
        ticker="INFY",
        company_name="Infosys",
        filing_date=datetime.now(timezone.utc)
    )

    assert res.has_financial_tables
    assert res.metadata.checksum is not None
