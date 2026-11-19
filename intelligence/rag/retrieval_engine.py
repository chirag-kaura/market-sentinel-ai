"""
Hybrid Filtered Retrieval Engine Module.
Phase 9 — Step 9.5: Combines exact ticker metadata filtering, temporal window constraints,
keyword BM25-style boosting, and semantic dense vector similarity to retrieve evidence.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import re
from typing import Dict, List, Optional, Set, Tuple
from intelligence.rag.vector_store import DocumentChunkVectorModel, VectorStoreRepository
from intelligence.rag.embedding_pipeline import CPUDenseEmbeddingPipeline


@dataclass(frozen=True)
class RetrievedEvidenceChunk:
    """A verified, evidence-grounded chunk retrieved for LLM prompt augmentation."""
    chunk_id: str
    ticker: str
    company_name: str
    section_title: str
    filing_date: datetime
    content: str
    similarity_score: float
    temporal_proximity_weight: float
    hybrid_score: float  # Composite metric combining semantic similarity and time proximity
    source_url: Optional[str]


class HybridFilteredRetrievalEngine:
    """
    Retrieves corporate disclosure evidence for surveillance alert investigations.
    Strictly filters out unrelated companies before performing dense vector search,
    preventing cross-company retrieval hallucinations.
    """

    def __init__(
        self,
        vector_repo: VectorStoreRepository,
        embedding_pipeline: CPUDenseEmbeddingPipeline,
        time_decay_halflife_days: float = 7.0
    ):
        self.repo = vector_repo
        self.embedder = embedding_pipeline
        self.time_decay_halflife_days = time_decay_halflife_days
        self._decay_lambda = math.log(2) / (self.time_decay_halflife_days * 86400)

    def retrieve_evidence(
        self,
        query: str,
        ticker: str,
        anchor_timestamp: datetime,
        lookback_days: float = 14.0,
        top_k: int = 3,
        min_hybrid_score: float = 0.30
    ) -> List[RetrievedEvidenceChunk]:
        """
        Executes hybrid retrieval:
        1. Ticker strict constraint.
        2. Temporal lookback window.
        3. Dense semantic cosine similarity.
        4. Time decay weighting.
        """
        if anchor_timestamp.tzinfo is None:
            anchor_timestamp = anchor_timestamp.replace(tzinfo=timezone.utc)

        # 1. Embed query
        query_vec = self.embedder.embed_text(query).vector

        # 2. Dense vector search constrained by ticker
        raw_candidates = self.repo.similarity_search(
            query_vector=query_vec,
            ticker=ticker,
            top_k=top_k * 4,  # Oversample before temporal filtering
            min_similarity=0.05
        )

        if not raw_candidates:
            return []

        retrieved: List[RetrievedEvidenceChunk] = []
        anchor_ts = anchor_timestamp.timestamp()
        max_lookback_secs = lookback_days * 86400

        for chunk_model, sim in raw_candidates:
            chunk_dt = chunk_model.filing_date
            if chunk_dt.tzinfo is None:
                chunk_dt = chunk_dt.replace(tzinfo=timezone.utc)

            delta_secs = anchor_ts - chunk_dt.timestamp()

            # Must be within permissible lookback window (and not in the future relative to anchor)
            if -86400 <= delta_secs <= max_lookback_secs:
                # Proximity weight: closer to anchor date gets higher weight
                time_weight = math.exp(-self._decay_lambda * max(0.0, delta_secs))

                # Exact lexical / BM25 term overlap boost (Issue 29: Hybrid Dense-Sparse Retrieval)
                query_tokens = {t for t in query.lower().split() if len(t) > 3}
                lexical_hits = sum(
                    1 for t in query_tokens
                    if t in chunk_model.content.lower() or t in chunk_model.section_title.lower()
                )
                lexical_ratio = (lexical_hits / max(1, len(query_tokens))) if query_tokens else 0.0

                # Hybrid score: 60% semantic similarity + 25% temporal proximity + 15% lexical match
                hybrid_score = round(
                    (0.60 * sim) + (0.25 * time_weight) + (0.15 * min(1.0, lexical_ratio * 2.0)), 4
                )

                if hybrid_score >= min_hybrid_score:
                    retrieved.append(
                        RetrievedEvidenceChunk(
                            chunk_id=chunk_model.chunk_id,
                            ticker=chunk_model.ticker,
                            company_name=chunk_model.company_name,
                            section_title=chunk_model.section_title,
                            filing_date=chunk_dt,
                            content=chunk_model.content,
                            similarity_score=sim,
                            temporal_proximity_weight=round(time_weight, 4),
                            hybrid_score=hybrid_score,
                            source_url=chunk_model.source_url
                        )
                    )

        # Sort by hybrid score descending
        retrieved.sort(key=lambda x: x.hybrid_score, reverse=True)
        return retrieved[:top_k]
