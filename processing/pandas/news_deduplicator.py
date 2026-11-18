"""News Deduplication and Syndicate Detection Module.

Identifies duplicate news articles, repeated syndicated stories, and identical headlines
using canonical URL normalization and cryptographic headline hashing.
"""
import hashlib
import logging
import re
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)


class NewsDeduplicator:
    """Detects and filters duplicate financial news stories."""

    @staticmethod
    def normalize_url(url: str) -> str:
        """Strip tracking query parameters (utm_*, ref, etc.) and fragments from URLs."""
        if not url:
            return ""
        parsed = urlparse(url.strip())
        # Strip tracking query parameters
        clean_query = "&".join(
            param for param in parsed.query.split("&")
            if not param.startswith(("utm_", "ref", "fbclid", "gclid", "src"))
        )
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            parsed.params,
            clean_query,
            "",  # Remove fragment
        ))
        return normalized

    @staticmethod
    def compute_headline_hash(title: str) -> str:
        """Generate MD5 hash of lowercase, alphanumeric-only headline for syndicate matching."""
        normalized_title = re.sub(r"[^a-zA-Z0-9]", "", title.lower())
        return hashlib.md5(normalized_title.encode("utf-8")).hexdigest()

    @classmethod
    def deduplicate_articles(
        cls,
        articles: List[Dict],
        existing_url_hashes: Optional[Set[str]] = None,
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """Deduplicate a list of raw article dictionaries.

        Returns:
            Tuple of (unique_articles, duplicate_articles, audit_metrics)
        """
        existing_url_hashes = existing_url_hashes or set()
        seen_urls: Set[str] = set()
        seen_headline_hashes: Set[str] = set()

        unique_articles = []
        duplicate_articles = []

        audit_metrics = {
            "total_input": len(articles),
            "exact_url_duplicates": 0,
            "syndicate_headline_duplicates": 0,
            "retained_unique": 0,
        }

        for art in articles:
            raw_url = art.get("canonical_url", "")
            title = art.get("title", "")

            norm_url = cls.normalize_url(raw_url)
            headline_hash = cls.compute_headline_hash(title)

            # Check exact URL duplication
            if norm_url in seen_urls or norm_url in existing_url_hashes:
                audit_metrics["exact_url_duplicates"] += 1
                duplicate_articles.append(art)
                continue

            # Check syndicated headline duplication
            if headline_hash in seen_headline_hashes:
                audit_metrics["syndicate_headline_duplicates"] += 1
                duplicate_articles.append(art)
                continue

            # Unique article
            seen_urls.add(norm_url)
            seen_headline_hashes.add(headline_hash)
            art["canonical_url"] = norm_url
            art["headline_hash"] = headline_hash
            unique_articles.append(art)

        audit_metrics["retained_unique"] = len(unique_articles)
        return unique_articles, duplicate_articles, audit_metrics
