"""
CPU-Friendly Dense Embeddings Pipeline Module.
Phase 9 — Step 9.3: Generates dense semantic vector embeddings (384 dimensions)
optimized for low-latency CPU inference with mock/offline fallback.
"""

from dataclasses import dataclass
import hashlib
import math
import re
from typing import List, Optional, Union
import numpy as np


@dataclass(frozen=True)
class EmbeddingResult:
    """Container for vector embedding outputs."""
    text: str
    vector: List[float]
    dimension: int
    is_mock: bool


class CPUDenseEmbeddingPipeline:
    """
    Lightweight, CPU-optimized embedding pipeline.
    Uses 'all-MiniLM-L6-v2' (384-dim) when sentence_transformers is available,
    with an ultra-fast deterministic hash-projection fallback for offline/isolated tests.
    """

    DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, force_cpu: bool = True, use_mock: bool = False):
        self.model_name = model_name
        self.force_cpu = force_cpu
        self.use_mock = use_mock
        self._model = None

        if not self.use_mock:
            try:
                from sentence_transformers import SentenceTransformer
                # Lazy load model only on first real request or initialization
                self._model = SentenceTransformer(self.model_name, device="cpu")
            except Exception:
                # Graceful fallback to deterministic mock embedding
                self.use_mock = True

    def embed_text(self, text: str) -> EmbeddingResult:
        """Embeds a single string into a normalized 384-dimensional dense vector."""
        vectors = self.embed_batch([text])
        return vectors[0]

    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Embeds a batch of strings efficiently."""
        if not texts:
            return []

        if not self.use_mock and self._model is not None:
            # Generate real embeddings via SentenceTransformer on CPU
            embeddings = self._model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            results = []
            for text, vec in zip(texts, embeddings):
                results.append(
                    EmbeddingResult(
                        text=text,
                        vector=vec.tolist(),
                        dimension=len(vec),
                        is_mock=False
                    )
                )
            return results
        else:
            # Deterministic, normalized 384-dimensional semantic projection
            results = []
            for text in texts:
                vec = self._generate_deterministic_vector(text, self.EMBEDDING_DIM)
                results.append(
                    EmbeddingResult(
                        text=text,
                        vector=vec,
                        dimension=self.EMBEDDING_DIM,
                        is_mock=True
                    )
                )
            return results

    @staticmethod
    def _generate_deterministic_vector(text: str, dim: int = 384) -> List[float]:
        """
        Generates a deterministic, bag-of-words weighted unit-normalized dense pseudo-vector.
        Enables genuine semantic similarity testing in offline/mock test environments.
        """
        tokens = [t.lower() for t in re.findall(r"\b\w+\b", text)]
        raw_vec = np.zeros(dim, dtype=np.float32)

        for token in tokens:
            token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:8], 16)
            rng = np.random.RandomState(token_hash % (2**31))
            raw_vec += rng.randn(dim).astype(np.float32)

        if len(tokens) == 0:
            raw_vec = np.ones(dim, dtype=np.float32)

        norm = np.linalg.norm(raw_vec)
        normalized = (raw_vec / norm).tolist() if norm > 0 else raw_vec.tolist()
        return [round(float(v), 6) for v in normalized]

    @staticmethod
    def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two unit vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))
