"""Unit tests for FinancialSentimentEngine (Phase 7 — Step 7.5)."""
import pytest
from intelligence.nlp.sentiment_engine import FinancialSentimentEngine, SentimentPolarity


@pytest.fixture
def sentiment_engine():
    return FinancialSentimentEngine(neutral_window=0.15)


def test_positive_financial_sentiment(sentiment_engine):
    headline = "Tata Motors Q3 profit jumps 25%, beats analyst forecasts"
    text = "Robust overseas revenue growth and strong JLR EBITDA margin expansion drove record performance."
    res = sentiment_engine.analyze(text, headline=headline)

    assert res.polarity == SentimentPolarity.POSITIVE
    assert res.compound_score > 0.20
    assert "profit" in res.top_positive_words or "jumps" in res.top_positive_words


def test_negative_financial_sentiment_with_investigation(sentiment_engine):
    headline = "Regulator slaps hefty penalty over severe disclosure violation and fraud probe"
    text = "Sharp decline in net earnings amid ongoing forensic investigation."
    res = sentiment_engine.analyze(text, headline=headline)

    assert res.polarity == SentimentPolarity.NEGATIVE
    assert res.compound_score < -0.20
    assert "penalty" in res.top_negative_words or "fraud" in res.top_negative_words or "probe" in res.top_negative_words


def test_negation_handling(sentiment_engine):
    text_pos = "Company reported growth and profit."
    text_negated = "Company reported no growth and failed to achieve profit."

    res_pos = sentiment_engine.analyze(text_pos)
    res_neg = sentiment_engine.analyze(text_negated)

    assert res_pos.compound_score > 0
    assert res_neg.compound_score < res_pos.compound_score
    assert any("not_" in w for w in res_neg.top_negative_words)


def test_uncertainty_quantification(sentiment_engine):
    text = "Rumors of potential merger remain uncertain amid pending regulatory approvals and high market volatility."
    res = sentiment_engine.analyze(text)

    assert res.uncertainty_score > 0.40


def test_neutral_factual_statement(sentiment_engine):
    text = "The annual general meeting of shareholders will be convened on July 14 at Mumbai corporate headquarters."
    res = sentiment_engine.analyze(text)

    assert res.polarity == SentimentPolarity.NEUTRAL
    assert abs(res.compound_score) <= 0.15
