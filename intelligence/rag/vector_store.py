"""
PostgreSQL pgvector Vector Storage and Indexing Module.
Phase 9 — Step 9.4: Establishes SQLAlchemy ORM schemas and vector similarity query
interfaces for document chunks stored in PostgreSQL with pgvector extension.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.types import JSON
from backend.models.market import Base


class DocumentChunkVectorModel(Base):
    """
    SQLAlchemy ORM model for storing financial document chunks and dense embeddings.
    Designed to leverage the PostgreSQL pgvector extension (384 dimensions)
    while maintaining cross-dialect testability via JSON array fallback.
    """
    __tablename__ = "document_chunks_vector"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(128), unique=True, nullable=False, index=True)
    doc_id = Column(String(64), nullable=False, index=True)
    ticker = Column(String(32), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    filing_date = Column(DateTime(timezone=True), nullable=False, index=True)
    section_title = Column(String(128), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    metadata_header = Column(String(512), nullable=False)
    source_url = Column(String(512), nullable=True)
    # Stored as JSON/Array of 384 floats (compatible with pgvector VECTOR(384) in PostgreSQL)
    embedding = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_doc_chunk_ticker_date", "ticker", "filing_date"),
    )


class VectorStoreRepository:
    """
    Repository for persisting and querying document chunks using cosine similarity.
    Supports in-memory/SQL filtering across company tickers and filing date horizons.
    """

    def __init__(self, session):
        self.session = session

    def insert_chunk(
        self,
        chunk_id: str,
        doc_id: str,
        ticker: str,
        company_name: str,
        filing_date: datetime,
        section_title: str,
        chunk_index: int,
        content: str,
        token_count: int,
        metadata_header: str,
        embedding: List[float],
        source_url: Optional[str] = None
    ) -> DocumentChunkVectorModel:
        """Persists a document chunk and its dense vector embedding."""
        if filing_date.tzinfo is None:
            filing_date = filing_date.replace(tzinfo=timezone.utc)

        record = DocumentChunkVectorModel(
            chunk_id=chunk_id,
            doc_id=doc_id,
            ticker=ticker,
            company_name=company_name,
            filing_date=filing_date,
            section_title=section_title,
            chunk_index=chunk_index,
            content=content,
            token_count=token_count,
            metadata_header=metadata_header,
            source_url=source_url,
            embedding=embedding
        )
        self.session.add(record)
        self.session.commit()
        return record

    def similarity_search(
        self,
        query_vector: List[float],
        ticker: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.50
    ) -> List[Tuple[DocumentChunkVectorModel, float]]:
        """
        Executes filtered cosine similarity search over stored vectors.
        Computes cosine distance using vector dot products.
        """
        query = self.session.query(DocumentChunkVectorModel)
        if ticker:
            query = query.filter(DocumentChunkVectorModel.ticker == ticker)

        candidates = query.all()
        if not candidates:
            return []

        import numpy as np
        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        scored_candidates: List[Tuple[DocumentChunkVectorModel, float]] = []
        for cand in candidates:
            c_vec = np.array(cand.embedding, dtype=np.float32)
            c_norm = np.linalg.norm(c_vec)
            if c_norm > 0:
                similarity = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
                if similarity >= min_similarity:
                    scored_candidates.append((cand, round(similarity, 4)))

        # Sort by similarity descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[:top_k]
