"""Unit tests for CPUDenseEmbeddingPipeline (Phase 9 — Step 9.3)."""
import pytest
from intelligence.rag.embedding_pipeline import CPUDenseEmbeddingPipeline


@pytest.fixture
def mock_pipeline():
    # Use mock pipeline for deterministic, lightning-fast unit tests
    return CPUDenseEmbeddingPipeline(use_mock=True)


def test_embedding_dimension_and_normalization(mock_pipeline):
    text = "Tata Motors reports record Q3 consolidated net profit on strong JLR demand."
    res = mock_pipeline.embed_text(text)

    assert res.dimension == 384
    assert len(res.vector) == 384
    assert res.is_mock

    # Verify unit norm: sum of squares should approximate 1.0
    sum_squares = sum(x**2 for x in res.vector)
    assert pytest.approx(sum_squares, 0.01) == 1.0


def test_batch_embedding(mock_pipeline):
    texts = [
        "Reliance acquires retail brand.",
        "SEBI issues insider trading penalty.",
        "Infosys signs multi-year digital transformation pact."
    ]
    results = mock_pipeline.embed_batch(texts)

    assert len(results) == 3
    for r in results:
        assert r.dimension == 384


def test_deterministic_cosine_similarity(mock_pipeline):
    text_a = "Quarterly results show strong EBITDA and revenue growth."
    text_b = "Quarterly results show strong EBITDA and revenue growth."
    text_c = "Meteorological department forecasts heavy monsoon rainfall."

    vec_a = mock_pipeline.embed_text(text_a).vector
    vec_b = mock_pipeline.embed_text(text_b).vector
    vec_c = mock_pipeline.embed_text(text_c).vector

    sim_identical = CPUDenseEmbeddingPipeline.compute_cosine_similarity(vec_a, vec_b)
    sim_unrelated = CPUDenseEmbeddingPipeline.compute_cosine_similarity(vec_a, vec_c)

    assert pytest.approx(sim_identical, 0.001) == 1.0
    assert sim_unrelated < 0.95
