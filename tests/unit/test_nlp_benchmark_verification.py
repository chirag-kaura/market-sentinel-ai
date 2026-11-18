"""
NLP Evaluation & Ground Truth Benchmark Test Suite.
Phase 7 — Step 7.7: Evaluates end-to-end NLP pipelines (cleaning, NER, ticker resolution,
event classification, sentiment, and novelty) against ground truth financial benchmarks.
"""

from datetime import datetime, timezone
import pytest
from intelligence.nlp import (
    FinancialTextCleaner,
    FinancialNERExtractor,
    EntityCategory,
    EntityTickerResolver,
    FinancialEventClassifier,
    FinancialEventType,
    FinancialSentimentEngine,
    SentimentPolarity,
    NewsNoveltyIntensityEngine
)


# Ground truth test cases representing Indian financial market scenarios
BENCHMARK_CASES = [
    {
        "id": "tc1_earnings",
        "raw_text": "MUMBAI (Reuters) - Tata Motors Q3 consolidated net profit rose 25.3% to Rs 7,025 crore, beating Street estimates on strong JLR margins.",
        "expected_ticker": "TATAMOTORS",
        "expected_event": FinancialEventType.EARNINGS_FINANCIALS,
        "expected_polarity": SentimentPolarity.POSITIVE,
        "expect_regulator": False
    },
    {
        "id": "tc2_regulatory_probe",
        "raw_text": "[PTI] NEW DELHI: SEBI has initiated an insider trading inquiry and forensic audit into alleged share price manipulation ahead of corporate results.",
        "expected_ticker": None,
        "expected_event": FinancialEventType.FRAUD_INVESTIGATION,
        "expected_polarity": SentimentPolarity.NEGATIVE,
        "expect_regulator": True
    },
    {
        "id": "tc3_merger",
        "raw_text": "Reliance Retail announces mega acquisition of FMCG entity for ₹5,000 crore cash deal.",
        "expected_ticker": "RELIANCE",
        "expected_event": FinancialEventType.MERGERS_ACQUISITIONS,
        "expected_polarity": SentimentPolarity.POSITIVE,
        "expect_regulator": False
    },
    {
        "id": "tc4_contract_win",
        "raw_text": "Infosys bags multi-year $1.2 billion digital transformation contract from European telecommunications major.",
        "expected_ticker": "INFY",
        "expected_event": FinancialEventType.CONTRACT_ORDER_WIN,
        "expected_polarity": SentimentPolarity.POSITIVE,
        "expect_regulator": False
    }
]


@pytest.fixture
def nlp_pipeline():
    cleaner = FinancialTextCleaner()
    ner = FinancialNERExtractor()
    resolver = EntityTickerResolver()
    classifier = FinancialEventClassifier()
    sentiment = FinancialSentimentEngine()
    novelty = NewsNoveltyIntensityEngine()
    return cleaner, ner, resolver, classifier, sentiment, novelty


def test_end_to_end_nlp_pipeline_benchmark(nlp_pipeline):
    cleaner, ner, resolver, classifier, sentiment, novelty = nlp_pipeline

    correct_events = 0
    correct_polarities = 0
    correct_tickers = 0

    for case in BENCHMARK_CASES:
        # 1. Clean Text
        cleaned = cleaner.clean(case["raw_text"])
        assert not cleaned.is_empty
        assert "Reuters" not in cleaned.cleaned_text
        assert "PTI" not in cleaned.cleaned_text

        # 2. Extract Entities
        entities = ner.extract_entities(cleaned.cleaned_text)

        # 3. Resolve Ticker
        resolved_ticker = None
        for ent in entities:
            if ent.category in [EntityCategory.ORGANIZATION, EntityCategory.TICKER]:
                res = resolver.resolve(ent.text, context_text=cleaned.cleaned_text)
                if res:
                    resolved_ticker = res.ticker
                    break

        if case["expected_ticker"]:
            assert resolved_ticker == case["expected_ticker"]
            correct_tickers += 1

        # Check Regulator extraction if expected
        if case["expect_regulator"]:
            reg_ents = [e for e in entities if e.category == EntityCategory.REGULATOR]
            assert len(reg_ents) > 0
            assert "SEBI" in [e.canonical_hint for e in reg_ents]

        # 4. Classify Event
        ev_res = classifier.classify(cleaned.cleaned_text)
        if ev_res.primary_event == case["expected_event"]:
            correct_events += 1

        # 5. Sentiment Analysis
        sent_res = sentiment.analyze(cleaned.cleaned_text)
        if sent_res.polarity == case["expected_polarity"]:
            correct_polarities += 1

        # 6. Novelty
        if resolved_ticker:
            nov_res = novelty.process_story(
                story_id=case["id"],
                ticker=resolved_ticker,
                headline=cleaned.cleaned_text,
                timestamp=datetime.now(timezone.utc),
                source="BenchmarkFeed",
                content_hash=cleaned.content_hash
            )
            assert nov_res.is_novel
            assert nov_res.novelty_score > 0.50

    # Ensure 100% benchmark accuracy across test scenarios
    assert correct_events == len(BENCHMARK_CASES)
    assert correct_polarities == len(BENCHMARK_CASES)
    assert correct_tickers == sum(1 for c in BENCHMARK_CASES if c["expected_ticker"] is not None)
