"""
Financial Named Entity Recognition (NER) Module.
Phase 7 — Step 7.2: High-precision extraction of company names, ticker symbols,
regulatory bodies, executive persons, and financial amounts from news and filings.
"""

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import List, Optional, Set


class EntityCategory(str, Enum):
    ORGANIZATION = "ORGANIZATION"
    TICKER = "TICKER"
    REGULATOR = "REGULATOR"
    PERSON = "PERSON"
    MONETARY_VALUE = "MONETARY_VALUE"
    PERCENTAGE = "PERCENTAGE"


@dataclass(frozen=True)
class ExtractedEntity:
    """Structured entity detected within text."""
    text: str
    category: EntityCategory
    start_pos: int
    end_pos: int
    confidence: float
    canonical_hint: Optional[str] = None


class FinancialNERExtractor:
    """
    Lightweight, deterministic, and CPU-efficient Financial Named Entity Recognizer.
    Tailored for Indian equity markets (NSE/BSE) and international financial press.
    """

    # Known regulatory bodies in financial journalism
    REGULATOR_NAMES = {
        "sebi": "SEBI",
        "securities and exchange board of india": "SEBI",
        "rbi": "RBI",
        "reserve bank of india": "RBI",
        "cci": "CCI",
        "competition commission of india": "CCI",
        "ed": "Enforcement Directorate",
        "enforcement directorate": "Enforcement Directorate",
        "cbi": "CBI",
        "nclt": "NCLT",
        "national company law tribunal": "NCLT",
        "sec": "SEC",
        "finra": "FINRA",
        "bse": "BSE",
        "nse": "NSE",
    }

    # Common corporate legal designators
    CORP_SUFFIXES = r"\b(?:Ltd|Limited|Corp|Corporation|Inc|Industries|Enterprises|Pvt|Private|Bank|Motors|Pharma|Power|Infra|Technologies|Consultancy|Services)\b"

    # Prominent Indian and global corporate entities
    KNOWN_COMPANIES = {
        "reliance industries": "RELIANCE",
        "reliance": "RELIANCE",
        "tata consultancy services": "TCS",
        "tcs": "TCS",
        "infosys": "INFY",
        "hdfc bank": "HDFCBANK",
        "hdfc": "HDFCBANK",
        "icici bank": "ICICIBANK",
        "icici": "ICICIBANK",
        "state bank of india": "SBIN",
        "sbi": "SBIN",
        "bharti airtel": "BHARTIARTL",
        "airtel": "BHARTIARTL",
        "tata motors": "TATAMOTORS",
        "itc": "ITC",
        "larsen & toubro": "LT",
        "l&t": "LT",
        "adani enterprises": "ADANIENT",
        "adani ports": "ADANIPORTS",
        "sun pharma": "SUNPHARMA",
        "wipro": "WIPRO",
        "hcl technologies": "HCLTECH",
        "hcl tech": "HCLTECH",
        "axis bank": "AXISBANK",
        "bajaj finance": "BAJFINANCE",
        "kotak mahindra bank": "KOTAKBANK",
    }

    # Regex patterns for financial quantities
    MONEY_PATTERN = re.compile(
        r"(?:(?:Rs\.?|INR|₹|\$|€|£)\s*[\d,]+(?:\.\d+)?(?:\s*(?:crore|lakh|cr|bn|mn|billion|million|trillion))?)|(?:[\d,]+(?:\.\d+)?\s*(?:crore|cr|billion|million)\s*(?:rupees|dollars|inr)?)",
        re.IGNORECASE
    )

    PERCENT_PATTERN = re.compile(
        r"(?:[-+]?\s*\d+(?:\.\d+)?\s*(?:%|percent|percentage points|bps))",
        re.IGNORECASE
    )

    # Ticker explicit tag pattern (e.g., "(NSE: TATAMOTORS)" or "[BSE: 500570]")
    TICKER_TAG_PATTERN = re.compile(
        r"\b(?:NSE|BSE|TICKER):\s*([A-Z0-9_\-]+)\b",
        re.IGNORECASE
    )

    # Executive person honorific patterns (e.g. "Chairman N. Chandrasekaran", "CEO Salil Parekh")
    PERSON_PATTERN = re.compile(
        r"\b(?:Mr\.|Ms\.|Dr\.|CEO|MD|Chairman|Managing Director|CFO)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b"
    )

    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extracts financial entities from text and returns structured annotations."""
        if not text or not text.strip():
            return []

        entities: List[ExtractedEntity] = []
        lowered_text = text.lower()

        # 1. Regulators
        for reg_key, reg_canonical in self.REGULATOR_NAMES.items():
            pattern = re.compile(r"\b" + re.escape(reg_key) + r"\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                entities.append(ExtractedEntity(
                    text=match.group(0),
                    category=EntityCategory.REGULATOR,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.98,
                    canonical_hint=reg_canonical
                ))

        # 2. Known Companies / Entities
        for comp_name, ticker in self.KNOWN_COMPANIES.items():
            pattern = re.compile(r"\b" + re.escape(comp_name) + r"\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                entities.append(ExtractedEntity(
                    text=match.group(0),
                    category=EntityCategory.ORGANIZATION,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.95,
                    canonical_hint=ticker
                ))

        # 3. Explicit Ticker Tags
        for match in self.TICKER_TAG_PATTERN.finditer(text):
            ticker_symbol = match.group(1).upper()
            entities.append(ExtractedEntity(
                text=match.group(0),
                category=EntityCategory.TICKER,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=1.0,
                canonical_hint=ticker_symbol
            ))

        # 4. Monetary Quantities
        for match in self.MONEY_PATTERN.finditer(text):
            entities.append(ExtractedEntity(
                text=match.group(0).strip(),
                category=EntityCategory.MONETARY_VALUE,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.92,
                canonical_hint=match.group(0).strip()
            ))

        # 5. Percentages
        for match in self.PERCENT_PATTERN.finditer(text):
            entities.append(ExtractedEntity(
                text=match.group(0).strip(),
                category=EntityCategory.PERCENTAGE,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.95,
                canonical_hint=match.group(0).strip()
            ))

        # 6. Key Persons / Executives
        for match in self.PERSON_PATTERN.finditer(text):
            entities.append(ExtractedEntity(
                text=match.group(1).strip(),
                category=EntityCategory.PERSON,
                start_pos=match.start(1),
                end_pos=match.end(1),
                confidence=0.88,
                canonical_hint=match.group(1).strip()
            ))

        # Sort and deduplicate overlapping spans (prefer longer match)
        return self._resolve_overlapping_entities(entities)

    @staticmethod
    def _resolve_overlapping_entities(entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Resolves overlapping entity spans by prioritizing span length and confidence."""
        if not entities:
            return []

        # Sort primarily by start position, then by span length descending
        sorted_ents = sorted(entities, key=lambda e: (e.start_pos, -(e.end_pos - e.start_pos)))
        resolved: List[ExtractedEntity] = []

        last_end = -1
        for ent in sorted_ents:
            if ent.start_pos >= last_end:
                resolved.append(ent)
                last_end = ent.end_pos
            else:
                # Overlap detected; check if the new candidate is longer or higher confidence
                current_prev = resolved[-1]
                if (ent.end_pos - ent.start_pos) > (current_prev.end_pos - current_prev.start_pos):
                    resolved[-1] = ent
                    last_end = ent.end_pos

        return resolved
