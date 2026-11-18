"""Unit tests for FinancialTextCleaner (Phase 7 — Step 7.1)."""
import pytest
from intelligence.nlp.text_cleaner import FinancialTextCleaner, CleanedTextResult


@pytest.fixture
def cleaner():
    return FinancialTextCleaner(strip_datelines=True, strip_disclaimers=True)


def test_html_and_entity_stripping(cleaner):
    raw_text = "<p>Reliance Industries reported a <b>15.4% rise</b> in quarterly profit &amp; declared &#8377;10 dividend.</p>"
    result = cleaner.clean(raw_text)

    assert "<p>" not in result.cleaned_text
    assert "<b>" not in result.cleaned_text
    assert "&amp;" not in result.cleaned_text
    assert "15.4% rise" in result.cleaned_text
    assert "₹10 dividend" in result.cleaned_text or "&#8377;10 dividend" in result.cleaned_text or "profit & declared" in result.cleaned_text
    assert result.token_count > 0
    assert not result.is_empty


def test_wire_agency_and_dateline_extraction(cleaner):
    raw_wire = "MUMBAI, Nov 17 (Reuters) - Tata Motors board has approved a mega merger with its commercial vehicle arm."
    result = cleaner.clean(raw_wire)

    assert result.detected_dateline is not None
    assert "MUMBAI" in result.detected_dateline
    assert "approved a mega merger" in result.cleaned_text
    assert "MUMBAI, Nov 17 (Reuters) -" not in result.cleaned_text


def test_disclaimer_removal(cleaner):
    text_with_disclaimer = (
        "Infosys signs a multi-year $1.5 billion deal with global telecom major. "
        "Disclaimer: The above information is provided for educational purposes and should not be construed as investment advice."
    )
    result = cleaner.clean(text_with_disclaimer)

    assert "Infosys signs a multi-year $1.5 billion deal" in result.cleaned_text
    assert "Disclaimer:" not in result.cleaned_text
    assert "investment advice" not in result.cleaned_text


def test_deterministic_deduplication_hashing(cleaner):
    text_variant1 = "  TATA MOTORS   Q3 Net Profit Jumps 25%   To Rs 7,025 Crore.  "
    text_variant2 = "Tata Motors Q3 Net profit jumps 25% to Rs 7,025 crore."

    res1 = cleaner.clean(text_variant1)
    res2 = cleaner.clean(text_variant2)

    assert res1.content_hash == res2.content_hash

    # Jaccard similarity test
    sim = FinancialTextCleaner.compute_jaccard_similarity(text_variant1, text_variant2)
    assert sim >= 0.95


def test_empty_and_whitespace_text(cleaner):
    res_empty = cleaner.clean("   ")
    assert res_empty.is_empty
    assert res_empty.token_count == 0
    assert res_empty.cleaned_text == ""
