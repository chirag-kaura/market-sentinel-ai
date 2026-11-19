"""
Entity-to-Ticker Standardized Resolution and Disambiguation Engine.
Phase 7 — Step 7.3: Maps recognized entity strings and aliases to standardized
exchange symbols (e.g., 'NSE:RELIANCE', 'BSE:500325') with confidence scoring.
"""

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class TickerResolution:
    """Result of mapping a textual entity to an equity ticker symbol."""
    raw_entity: str
    ticker: str
    company_name: str
    exchange: str
    confidence: float
    is_ambiguous: bool
    alternative_tickers: Tuple[str, ...]


class EntityTickerResolver:
    """
    Resolves corporate names, acronyms, and media references to canonical stock tickers.
    Handles ambiguous entities (e.g. 'Tata', 'Adani', 'Reliance') using context hints.
    """

    # Canonical mapping database: Ticker -> metadata
    TICKER_REGISTRY = {
        "RELIANCE": {
            "name": "Reliance Industries Limited",
            "exchange": "NSE",
            "aliases": ["reliance", "ril", "reliance industries", "reliance ind", "jio parent", "mukesh ambani firm"],
            "sector": "Energy & Petrochemicals"
        },
        "TCS": {
            "name": "Tata Consultancy Services Limited",
            "exchange": "NSE",
            "aliases": ["tcs", "tata consultancy services", "tata consultancy", "tata consult"],
            "sector": "Information Technology"
        },
        "INFY": {
            "name": "Infosys Limited",
            "exchange": "NSE",
            "aliases": ["infosys", "infy", "infosys technologies", "infosys ltd"],
            "sector": "Information Technology"
        },
        "HDFCBANK": {
            "name": "HDFC Bank Limited",
            "exchange": "NSE",
            "aliases": ["hdfc bank", "hdfc", "housing development finance corporation bank"],
            "sector": "Banking & Financial Services"
        },
        "ICICIBANK": {
            "name": "ICICI Bank Limited",
            "exchange": "NSE",
            "aliases": ["icici bank", "icici"],
            "sector": "Banking & Financial Services"
        },
        "TATAMOTORS": {
            "name": "Tata Motors Limited",
            "exchange": "NSE",
            "aliases": ["tata motors", "tamo", "tata commercial vehicles", "jlr parent"],
            "sector": "Automobile"
        },
        "SBIN": {
            "name": "State Bank of India",
            "exchange": "NSE",
            "aliases": ["sbi", "state bank of india", "state bank"],
            "sector": "Banking & Financial Services"
        },
        "BHARTIARTL": {
            "name": "Bharti Airtel Limited",
            "exchange": "NSE",
            "aliases": ["airtel", "bharti airtel", "bharti airtel ltd"],
            "sector": "Telecommunications"
        },
        "ITC": {
            "name": "ITC Limited",
            "exchange": "NSE",
            "aliases": ["itc", "itc limited", "itc ltd"],
            "sector": "Consumer Goods"
        },
        "LT": {
            "name": "Larsen & Toubro Limited",
            "exchange": "NSE",
            "aliases": ["l&t", "lt", "larsen & toubro", "larsen and toubro"],
            "sector": "Engineering & Construction"
        },
        # Ambiguity parent groups
        "TATAPOWER": {
            "name": "Tata Power Company Limited",
            "exchange": "NSE",
            "aliases": ["tata power"],
            "sector": "Power"
        },
        "TATASTEEL": {
            "name": "Tata Steel Limited",
            "exchange": "NSE",
            "aliases": ["tata steel"],
            "sector": "Metals"
        }
    }

    # Conglomerate ambiguous roots mapping to potential children
    CONGLOMERATE_GROUPS = {
        "tata": ["TATAMOTORS", "TCS", "TATASTEEL", "TATAPOWER"],
        "reliance": ["RELIANCE"],
    }

    def __init__(self, min_similarity_threshold: float = 0.80):
        self.min_similarity_threshold = min_similarity_threshold
        # Invert aliases for fast exact lookup
        self._alias_index: Dict[str, str] = {}
        for ticker, meta in self.TICKER_REGISTRY.items():
            self._alias_index[ticker.lower()] = ticker
            for alias in meta["aliases"]:
                self._alias_index[alias.lower()] = ticker

    def resolve(self, raw_entity: str, context_text: Optional[str] = None) -> Optional[TickerResolution]:
        """
        Resolves an entity string to a stock ticker symbol.
        Uses context_text to disambiguate conglomerate family names.
        """
        if not raw_entity or not raw_entity.strip():
            return None

        clean_entity = raw_entity.strip().lower()

        # Guard against short generic tokens (e.g. 'it', 'lt') unless exact uppercase or financial context
        if len(clean_entity) <= 2 and not raw_entity.strip().isupper():
            if not context_text or not any(k in context_text.lower() for k in ["stock", "share", "equity", "nse", "bse", "quarter", "results", "board"]):
                return None

        # 1. Exact Match via Alias Index
        if clean_entity in self._alias_index:
            ticker = self._alias_index[clean_entity]
            meta = self.TICKER_REGISTRY[ticker]
            return TickerResolution(
                raw_entity=raw_entity,
                ticker=ticker,
                company_name=meta["name"],
                exchange=meta["exchange"],
                confidence=1.0,
                is_ambiguous=False,
                alternative_tickers=()
            )

        # 2. Conglomerate Root Disambiguation (e.g. standalone "Tata" with context)
        if clean_entity in self.CONGLOMERATE_GROUPS:
            candidates = self.CONGLOMERATE_GROUPS[clean_entity]
            if context_text:
                ctx_lower = context_text.lower()
                for cand in candidates:
                    cand_meta = self.TICKER_REGISTRY[cand]
                    # Check if sector or secondary alias is mentioned in context
                    if any(a in ctx_lower for a in cand_meta["aliases"]) or cand_meta["sector"].lower() in ctx_lower:
                        return TickerResolution(
                            raw_entity=raw_entity,
                            ticker=cand,
                            company_name=cand_meta["name"],
                            exchange=cand_meta["exchange"],
                            confidence=0.85,
                            is_ambiguous=True,
                            alternative_tickers=tuple(c for c in candidates if c != cand)
                        )
            # Default to primary conglomerate ticker with lower confidence
            primary = candidates[0]
            meta = self.TICKER_REGISTRY[primary]
            return TickerResolution(
                raw_entity=raw_entity,
                ticker=primary,
                company_name=meta["name"],
                exchange=meta["exchange"],
                confidence=0.55,
                is_ambiguous=True,
                alternative_tickers=tuple(candidates[1:])
            )

        # 3. Fuzzy String Match across aliases
        best_ticker: Optional[str] = None
        best_score = 0.0

        for alias, ticker in self._alias_index.items():
            sim = SequenceMatcher(None, clean_entity, alias).ratio()
            if sim > best_score:
                best_score = sim
                best_ticker = ticker

        if best_ticker and best_score >= self.min_similarity_threshold:
            meta = self.TICKER_REGISTRY[best_ticker]
            return TickerResolution(
                raw_entity=raw_entity,
                ticker=best_ticker,
                company_name=meta["name"],
                exchange=meta["exchange"],
                confidence=round(best_score, 3),
                is_ambiguous=False,
                alternative_tickers=()
            )

        return None
