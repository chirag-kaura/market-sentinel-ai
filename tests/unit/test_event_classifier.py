"""Unit tests for FinancialEventClassifier (Phase 7 — Step 7.4)."""
import pytest
from intelligence.nlp.event_classifier import FinancialEventClassifier, FinancialEventType


@pytest.fixture
def classifier():
    return FinancialEventClassifier()


def test_fraud_investigation_classification(classifier):
    text = "SEBI initiates forensic audit and inquiry over alleged insider trading and fund siphoning."
    res = classifier.classify(text)

    assert res.primary_event == FinancialEventType.FRAUD_INVESTIGATION
    assert "insider trading" in res.trigger_keywords or "forensic audit" in res.trigger_keywords
    assert res.surveillance_relevance >= 0.80
    assert res.confidence >= 0.70


def test_earnings_financials_classification(classifier):
    headline = "Tata Motors Q3 net profit rises 25% to Rs 7,025 crore"
    text = "Quarterly results beat estimates on strong JLR margins and revenue growth."
    res = classifier.classify(text, headline=headline)

    assert res.primary_event == FinancialEventType.EARNINGS_FINANCIALS
    assert res.confidence >= 0.70


def test_regulatory_action_classification(classifier):
    text = "Regulator issues penalty and bars promoter from securities market over disclosure violation."
    res = classifier.classify(text)

    assert res.primary_event in [FinancialEventType.REGULATORY_ACTION, FinancialEventType.FRAUD_INVESTIGATION]
    assert res.surveillance_relevance >= 0.70


def test_mergers_and_acquisitions_classification(classifier):
    text = "Reliance Retail announces acquisition of 51% stake in FMCG brand, open offer triggered."
    res = classifier.classify(text)

    assert res.primary_event == FinancialEventType.MERGERS_ACQUISITIONS
    assert "acquisition" in res.trigger_keywords or "open offer" in res.trigger_keywords


def test_unrelated_general_market_fallback(classifier):
    text = "Sunny weather across major metropolitan cities during the winter morning hours."
    res = classifier.classify(text)

    assert res.primary_event == FinancialEventType.GENERAL_MARKET
    assert res.surveillance_relevance <= 0.20
