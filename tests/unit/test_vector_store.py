"""Unit tests for VectorStoreRepository and DocumentChunkVectorModel (Phase 9 — Step 9.4)."""
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from intelligence.rag.vector_store import DocumentChunkVectorModel, VectorStoreRepository
from intelligence.rag.embedding_pipeline import CPUDenseEmbeddingPipeline


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


def test_insert_and_filtered_similarity_search(repo, embedder):
    t0 = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)

    # 1. Insert Reliance chunk
    rel_text = "Reliance Industries Q3 EBITDA surges 15% on robust retail margins."
    rel_vec = embedder.embed_text(rel_text).vector
    repo.insert_chunk(
        chunk_id="chk_ril_001",
        doc_id="doc_ril",
        ticker="RELIANCE",
        company_name="Reliance Industries",
        filing_date=t0,
        section_title="Financial Results",
        chunk_index=1,
        content=rel_text,
        token_count=10,
        metadata_header="[Company: Reliance | Ticker: RELIANCE]",
        embedding=rel_vec
    )

    # 2. Insert Infosys chunk
    infy_text = "Infosys announces multi-year digital transformation contract in Europe."
    infy_vec = embedder.embed_text(infy_text).vector
    repo.insert_chunk(
        chunk_id="chk_infy_001",
        doc_id="doc_infy",
        ticker="INFY",
        company_name="Infosys",
        filing_date=t0,
        section_title="Contract Announcement",
        chunk_index=1,
        content=infy_text,
        token_count=9,
        metadata_header="[Company: Infosys | Ticker: INFY]",
        embedding=infy_vec
    )

    # Query with identical Reliance text
    query_vec = embedder.embed_text(rel_text).vector
    results = repo.similarity_search(query_vec, ticker="RELIANCE", top_k=2)

    assert len(results) == 1
    top_chunk, sim = results[0]
    assert top_chunk.ticker == "RELIANCE"
    assert top_chunk.chunk_id == "chk_ril_001"
    assert pytest.approx(sim, 0.001) == 1.0


def test_empty_search_results_with_ticker_filter(repo, embedder):
    query_vec = embedder.embed_text("Arbitrary text").vector
    results = repo.similarity_search(query_vec, ticker="NON_EXISTENT", top_k=5)
    assert len(results) == 0
