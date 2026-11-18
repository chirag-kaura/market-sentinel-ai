"""Unit tests for FinancialTextChunker (Phase 9 — Step 9.2)."""
from datetime import datetime, timezone
import pytest
from intelligence.rag.document_parser import FinancialDocumentParser
from intelligence.rag.chunking_engine import FinancialTextChunker


@pytest.fixture
def parser():
    return FinancialDocumentParser()


@pytest.fixture
def chunker():
    return FinancialTextChunker(target_chunk_tokens=50, chunk_overlap_tokens=15)


def test_document_chunking_with_metadata_headers(parser, chunker):
    raw_filing = (
        "Financial Results\n"
        "Reliance Industries reported record quarterly EBITDA growth across oil-to-chemicals and consumer retail segments. "
        "Consolidated revenue stood at Rs 2,45,000 crore compared to Rs 2,20,000 crore in the previous year. "
        "Digital services recorded robust average revenue per user (ARPU) expansion reaching Rs 181. "
        "Net profit rose 12.5% YoY to Rs 19,320 crore on strong gross refining margins. "
        "Capital expenditure for the quarter was directed towards green energy gigafactory infrastructure in Jamnagar."
    )

    t0 = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
    parsed = parser.parse_document(
        doc_id="DOC_CHUNK_001",
        raw_text=raw_filing,
        ticker="RELIANCE",
        company_name="Reliance Industries",
        filing_date=t0
    )

    chunks = chunker.chunk_document(parsed)

    assert len(chunks) >= 1
    first_chunk = chunks[0]
    assert first_chunk.ticker == "RELIANCE"
    assert first_chunk.section_title == "Financial Results"
    assert "Company: Reliance Industries" in first_chunk.metadata_header
    assert "Ticker: RELIANCE" in first_chunk.metadata_header
    assert "2026-11-17" in first_chunk.metadata_header
    assert first_chunk.token_count > 0


def test_chunking_overlap_preservation(parser):
    # Test that consecutive chunks share overlap sentences
    chunker_small = FinancialTextChunker(target_chunk_tokens=20, chunk_overlap_tokens=10)
    text = (
        "Financial Results\n"
        "Sentence one describes first quarter revenue growth. "
        "Sentence two details margin expansion across international units. "
        "Sentence three highlights dividend payout to shareholders. "
        "Sentence four covers future forward guidance."
    )
    parsed = parser.parse_document(
        doc_id="DOC_OVERLAP_001",
        raw_text=text,
        ticker="TCS",
        company_name="TCS",
        filing_date=datetime.now(timezone.utc)
    )

    chunks = chunker_small.chunk_document(parsed)
    assert len(chunks) >= 2
