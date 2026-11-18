"""Unit tests for HybridFilteredRetrievalEngine (Phase 9 — Step 9.5)."""
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from intelligence.rag.vector_store import DocumentChunkVectorModel, VectorStoreRepository
from intelligence.rag.embedding_pipeline import CPUDenseEmbeddingPipeline
from intelligence.rag.retrieval_engine import HybridFilteredRetrievalEngine


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    DocumentChunkVectorModel.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repo(db_session):
    return VectorStoreRepository(session=db_session)


@pytest.fixture
def embedder():
    return CPUDenseEmbeddingPipeline(use_mock=True)


@pytest.fixture
def retrieval_engine(repo, embedder):
    return HybridFilteredRetrievalEngine(vector_repo=repo, embedding_pipeline=embedder)


def test_hybrid_filtered_retrieval(repo, embedder, retrieval_engine):
    t_anchor = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)

    # Insert historical chunks for TATAMOTORS
    t_recent = t_anchor - timedelta(days=2)
    t_old = t_anchor - timedelta(days=45)

    recent_text = "Tata Motors Q3 earnings highlight robust commercial vehicle margins."
    repo.insert_chunk(
        chunk_id="chk_tm_recent",
        doc_id="doc_tm_1",
        ticker="TATAMOTORS",
        company_name="Tata Motors",
        filing_date=t_recent,
        section_title="Financial Results",
        chunk_index=1,
        content=recent_text,
        token_count=10,
        metadata_header="[Tata Motors | 2026-11-15]",
        embedding=embedder.embed_text(recent_text).vector
    )

    old_text = "Tata Motors historical AGM notice from last year."
    repo.insert_chunk(
        chunk_id="chk_tm_old",
        doc_id="doc_tm_old",
        ticker="TATAMOTORS",
        company_name="Tata Motors",
        filing_date=t_old,
        section_title="AGM",
        chunk_index=1,
        content=old_text,
        token_count=8,
        metadata_header="[Tata Motors | Old]",
        embedding=embedder.embed_text(old_text).vector
    )

    # Insert chunk for unrelated ticker RELIANCE
    rel_text = "Reliance announces retail expansion."
    repo.insert_chunk(
        chunk_id="chk_ril",
        doc_id="doc_ril_1",
        ticker="RELIANCE",
        company_name="Reliance",
        filing_date=t_recent,
        section_title="Retail",
        chunk_index=1,
        content=rel_text,
        token_count=5,
        metadata_header="[Reliance]",
        embedding=embedder.embed_text(rel_text).vector
    )

    # Retrieve for TATAMOTORS with 14-day lookback
    evidence = retrieval_engine.retrieve_evidence(
        query="commercial vehicle earnings",
        ticker="TATAMOTORS",
        anchor_timestamp=t_anchor,
        lookback_days=14.0,
        top_k=3
    )

    # Should only return recent TATAMOTORS chunk, filtering out 45-day old chunk and RELIANCE chunk
    assert len(evidence) == 1
    top_ev = evidence[0]
    assert top_ev.ticker == "TATAMOTORS"
    assert top_ev.chunk_id == "chk_tm_recent"
    assert top_ev.hybrid_score > 0.40
    assert top_ev.temporal_proximity_weight > 0.70
