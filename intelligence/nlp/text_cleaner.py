"""
Financial Text Preprocessing and Cleaning Module.
Phase 7 — Step 7.1: Converts raw, unstructured news headlines and corporate disclosures
into pristine, normalized, and deduplicated text representation.
"""

from dataclasses import dataclass
import hashlib
import html
import re
import unicodedata
from typing import Optional, Set, Tuple


@dataclass(frozen=True)
class CleanedTextResult:
    """Immutable structured container for cleaned text and metadata."""
    original_text: str
    cleaned_text: str
    cleaned_title: Optional[str]
    detected_dateline: Optional[str]
    detected_agency: Optional[str]
    token_count: int
    content_hash: str
    is_empty: bool


class FinancialTextCleaner:
    """
    High-performance, CPU-friendly text cleaner designed specifically for
    financial headlines, exchange disclosures (BSE/NSE), and wire feeds (PTI, Reuters, Bloomberg).
    """

    # Common wire agency signatures in financial reporting
    AGENCY_PATTERNS = [
        re.compile(r"^\s*\[?(?:PTI|PRESS TRUST OF INDIA)\]?\s*(?:[:-]|\b)\s*", re.IGNORECASE),
        re.compile(r"^\s*\[?(?:REUTERS)\]?\s*(?:[:-]|\b)\s*", re.IGNORECASE),
        re.compile(r"^\s*\[?(?:BLOOMBERG)\]?\s*(?:[:-]|\b)\s*", re.IGNORECASE),
        re.compile(r"^\s*\[?(?:ANI)\]?\s*(?:[:-]|\b)\s*", re.IGNORECASE),
        re.compile(r"^\s*\[?(?:BSE(?:\s+DISCLOSURE)?)\]?\s*(?:[:-]|\b)\s*", re.IGNORECASE),
        re.compile(r"^\s*\[?(?:NSE(?:\s+ANNOUNCEMENT)?)\]?\s*(?:[:-]|\b)\s*", re.IGNORECASE),
    ]

    # Dateline pattern: requires an all-caps city name followed by date/agency and hyphen or colon
    # e.g. "MUMBAI, Nov 17 (Reuters) - " or "NEW DELHI: " or "MUMBAI - "
    DATELINE_PATTERN = re.compile(
        r"^\s*([A-Z]{3,15}(?:\s+[A-Z]{3,15})?(?:,\s*[A-Za-z0-9\s]{3,15})?)\s*(?:\((?:Reuters|PTI|Bloomberg|ANI|CNBC)\))?\s*(?:[-—]|:\s*(?=[A-Z]))\s*"
    )

    # Common boilerplate disclaimers at the bottom of financial disclosures/articles
    DISCLAIMER_PATTERNS = [
        re.compile(r"\b(?:disclaimer|note):\s*.*$", re.IGNORECASE | re.DOTALL),
        re.compile(r"\b(?:for\s+further\s+details|source:)\s*please\s+refer\s+to.*$", re.IGNORECASE | re.DOTALL),
        re.compile(r"\b(?:copyright|all\s+rights\s+reserved).*$", re.IGNORECASE | re.DOTALL),
    ]

    # HTML tags stripper
    HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

    # Multiple whitespace matcher
    WHITESPACE_PATTERN = re.compile(r"\s+")

    def __init__(self, strip_datelines: bool = True, strip_disclaimers: bool = True):
        self.strip_datelines = strip_datelines
        self.strip_disclaimers = strip_disclaimers

    def clean(self, text: str, title: Optional[str] = None) -> CleanedTextResult:
        """
        Cleans and normalizes news body text and an optional headline/title.
        """
        if not text or not text.strip():
            return CleanedTextResult(
                original_text=text or "",
                cleaned_text="",
                cleaned_title=self.clean_title(title) if title else None,
                detected_dateline=None,
                detected_agency=None,
                token_count=0,
                content_hash=self._hash_text(""),
                is_empty=True
            )

        original_text = text
        working_text = html.unescape(text)

        # 1. Strip raw HTML markup
        working_text = self.HTML_TAG_PATTERN.sub(" ", working_text)

        # 2. Normalize Unicode (e.g., non-breaking spaces, curly quotes)
        working_text = unicodedata.normalize("NFKC", working_text)
        working_text = working_text.replace("‘", "'").replace("’", "'")
        working_text = working_text.replace("“", '"').replace("”", '"')
        working_text = working_text.replace("—", " - ").replace("–", " - ")

        # 3. Detect and extract wire agency
        detected_agency = None
        for pattern in self.AGENCY_PATTERNS:
            match = pattern.search(working_text)
            if match:
                detected_agency = match.group(0).strip("[] :-")
                if self.strip_datelines:
                    working_text = pattern.sub("", working_text)
                break

        # 4. Detect and extract dateline
        detected_dateline = None
        dateline_match = self.DATELINE_PATTERN.search(working_text)
        if dateline_match:
            detected_dateline = dateline_match.group(1).strip()
            if self.strip_datelines:
                working_text = self.DATELINE_PATTERN.sub("", working_text)

        # 5. Remove legal disclaimers / footers
        if self.strip_disclaimers:
            for disc_pattern in self.DISCLAIMER_PATTERNS:
                working_text = disc_pattern.sub("", working_text)

        # 6. Normalize whitespace
        cleaned = self.WHITESPACE_PATTERN.sub(" ", working_text).strip()

        # 7. Compute tokens and normalized deduplication hash
        tokens = cleaned.split()
        token_count = len(tokens)
        content_hash = self._hash_text(cleaned)
        cleaned_title = self.clean_title(title) if title else None

        return CleanedTextResult(
            original_text=original_text,
            cleaned_text=cleaned,
            cleaned_title=cleaned_title,
            detected_dateline=detected_dateline,
            detected_agency=detected_agency,
            token_count=token_count,
            content_hash=content_hash,
            is_empty=token_count == 0
        )

    def clean_title(self, title: Optional[str]) -> Optional[str]:
        """Cleans and standardizes headline titles."""
        if not title:
            return None
        t = html.unescape(title)
        t = self.HTML_TAG_PATTERN.sub(" ", t)
        t = unicodedata.normalize("NFKC", t)
        t = t.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
        # Remove leading agency markers like "PTI: " or "[Reuters]"
        for pattern in self.AGENCY_PATTERNS:
            t = pattern.sub("", t)
        return self.WHITESPACE_PATTERN.sub(" ", t).strip()

    @staticmethod
    def _hash_text(text: str) -> str:
        """Generates deterministic MD5 hash of lowercased, whitespace-normalized text."""
        normalized = "".join(text.lower().split())
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_jaccard_similarity(text_a: str, text_b: str) -> float:
        """Computes word-level Jaccard similarity for near-duplicate headline detection."""
        tokens_a: Set[str] = set(re.findall(r"\b\w+\b", text_a.lower()))
        tokens_b: Set[str] = set(re.findall(r"\b\w+\b", text_b.lower()))
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        return len(intersection) / len(union)
