"""Unit tests for FinancialNERExtractor (Phase 7 — Step 7.2)."""
import pytest
from intelligence.nlp.entity_recognizer import FinancialNERExtractor, EntityCategory


@pytest.fixture
def extractor():
    return FinancialNERExtractor()


def test_company_and_ticker_tag_extraction(extractor):
    text = "Tata Motors shares surged after company reported Q3 earnings. (NSE: TATAMOTORS)"
    entities = extractor.extract_entities(text)

    categories = [e.category for e in entities]
    assert EntityCategory.ORGANIZATION in categories
    assert EntityCategory.TICKER in categories

    tata_org = next(e for e in entities if e.category == EntityCategory.ORGANIZATION)
    assert tata_org.canonical_hint == "TATAMOTORS"

    ticker_ent = next(e for e in entities if e.category == EntityCategory.TICKER)
    assert ticker_ent.canonical_hint == "TATAMOTORS"


def test_regulatory_body_extraction(extractor):
    text = "SEBI issues show-cause notice to leading brokerage over algorithmic trading compliance."
    entities = extractor.extract_entities(text)

    reg_ent = next((e for e in entities if e.category == EntityCategory.REGULATOR), None)
    assert reg_ent is not None
    assert reg_ent.canonical_hint == "SEBI"


def test_financial_quantities_and_percentages(extractor):
    text = "Reliance Industries announced an investment of ₹75,000 crore, raising guidance by +12.5%."
    entities = extractor.extract_entities(text)

    money_ents = [e for e in entities if e.category == EntityCategory.MONETARY_VALUE]
    pct_ents = [e for e in entities if e.category == EntityCategory.PERCENTAGE]

    assert len(money_ents) >= 1
    assert any("75,000" in e.text for e in money_ents)

    assert len(pct_ents) >= 1
    assert any("12.5%" in e.text for e in pct_ents)


def test_executive_person_extraction(extractor):
    text = "CEO Salil Parekh highlighted strong cloud revenue growth across European client accounts."
    entities = extractor.extract_entities(text)

    person_ent = next((e for e in entities if e.category == EntityCategory.PERSON), None)
    assert person_ent is not None
    assert "Salil Parekh" in person_ent.text


def test_overlap_resolution(extractor):
    # Tests that 'Tata Consultancy Services' is preferred over standalone 'TCS' if both match or overlap
    text = "Tata Consultancy Services won an IT modernization contract."
    entities = extractor.extract_entities(text)

    org_ents = [e for e in entities if e.category == EntityCategory.ORGANIZATION]
    assert len(org_ents) == 1
    assert org_ents[0].text == "Tata Consultancy Services"
    assert org_ents[0].canonical_hint == "TCS"
