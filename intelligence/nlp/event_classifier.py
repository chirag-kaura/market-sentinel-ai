"""
Financial Event Classification Engine.
Phase 7 — Step 7.4: Classifies news stories and regulatory filings into
structured surveillance event categories (Earnings, M&A, Regulatory, Fraud/Investigation, Management).
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Dict, List, Optional, Tuple


class FinancialEventType(str, Enum):
    EARNINGS_FINANCIALS = "EARNINGS_FINANCIALS"
    MERGERS_ACQUISITIONS = "MERGERS_ACQUISITIONS"
    REGULATORY_ACTION = "REGULATORY_ACTION"
    FRAUD_INVESTIGATION = "FRAUD_INVESTIGATION"
    EXECUTIVE_LEADERSHIP = "EXECUTIVE_LEADERSHIP"
    CONTRACT_ORDER_WIN = "CONTRACT_ORDER_WIN"
    CAPITAL_RESTRUCTURING = "CAPITAL_RESTRUCTURING"
    GENERAL_MARKET = "GENERAL_MARKET"


@dataclass(frozen=True)
class EventClassificationResult:
    """Structured result of financial event classification."""
    primary_event: FinancialEventType
    confidence: float
    secondary_events: Tuple[FinancialEventType, ...]
    trigger_keywords: Tuple[str, ...]
    surveillance_relevance: float  # Scale 0.0 (low) to 1.0 (extreme investigation interest)


class FinancialEventClassifier:
    """
    Lightweight, multi-category rule and keyword density classifier for financial events.
    Prioritizes regulatory enforcement, fraud inquiries, and major corporate actions.
    """

    # Lexicon mapping event categories to characteristic keyword patterns and weights
    EVENT_LEXICONS: Dict[FinancialEventType, Dict[str, float]] = {
        FinancialEventType.FRAUD_INVESTIGATION: {
            "fraud": 1.5, "bribe": 1.5, "bribery": 1.5, "scam": 1.5, "insider trading": 2.0,
            "manipulation": 1.8, "money laundering": 1.8, "forgery": 1.5, "whistleblower": 1.6,
            "forensic audit": 1.8, "raids": 1.4, "arrested": 1.5, "siphoning": 1.8, "ed search": 1.6
        },
        FinancialEventType.REGULATORY_ACTION: {
            "show cause": 1.5, "penalty": 1.4, "penalized": 1.4, "bar": 1.3, "barred": 1.5,
            "banned": 1.5, "sebi order": 1.8, "investigation": 1.3, "scrutiny": 1.2,
            "violation": 1.4, "fine": 1.1, "adjudication": 1.4, "warning": 1.1, "curbs": 1.3
        },
        FinancialEventType.MERGERS_ACQUISITIONS: {
            "acquisition": 1.4, "acquires": 1.4, "merger": 1.5, "takeover": 1.5,
            "buyout": 1.4, "stake buy": 1.3, "amalgamation": 1.4, "divestment": 1.3,
            "demerger": 1.4, "open offer": 1.5, "consolidation": 1.2
        },
        FinancialEventType.EARNINGS_FINANCIALS: {
            "q1": 1.0, "q2": 1.0, "q3": 1.0, "q4": 1.0, "quarterly results": 1.5,
            "net profit": 1.3, "revenue": 1.1, "ebitda": 1.2, "margin": 1.1,
            "earnings": 1.3, "guidance": 1.2, "dividend": 1.2, "annual profit": 1.3
        },
        FinancialEventType.CONTRACT_ORDER_WIN: {
            "order win": 1.5, "bags contract": 1.5, "awarded contract": 1.5, "deal worth": 1.4,
            "secures order": 1.5, "partnership": 1.1, "multi-year agreement": 1.4, "pact": 1.2,
            "contract": 1.3, "deal": 1.1, "bags": 1.3, "secures": 1.2
        },
        FinancialEventType.EXECUTIVE_LEADERSHIP: {
            "resigns": 1.4, "resignation": 1.4, "appointed ceo": 1.5, "new md": 1.4,
            "steps down": 1.4, "board reshuffle": 1.3, "independent director": 1.2
        },
        FinancialEventType.CAPITAL_RESTRUCTURING: {
            "rights issue": 1.4, "buyback": 1.4, "qip": 1.4, "bonus issue": 1.3,
            "stock split": 1.3, "fund raise": 1.2, "preferential allotment": 1.4
        }
    }

    # Inherent surveillance importance multiplier per category
    SURVEILLANCE_MULTIPLIERS: Dict[FinancialEventType, float] = {
        FinancialEventType.FRAUD_INVESTIGATION: 1.0,
        FinancialEventType.REGULATORY_ACTION: 0.90,
        FinancialEventType.MERGERS_ACQUISITIONS: 0.75,
        FinancialEventType.CAPITAL_RESTRUCTURING: 0.65,
        FinancialEventType.EXECUTIVE_LEADERSHIP: 0.60,
        FinancialEventType.EARNINGS_FINANCIALS: 0.50,
        FinancialEventType.CONTRACT_ORDER_WIN: 0.40,
        FinancialEventType.GENERAL_MARKET: 0.15,
    }

    def classify(self, text: str, headline: Optional[str] = None) -> EventClassificationResult:
        """Classifies text into primary and secondary financial event categories."""
        combined_text = f"{headline or ''} {text}".lower()

        scores: Dict[FinancialEventType, float] = {}
        matched_keywords: Dict[FinancialEventType, List[str]] = {}

        for event_type, lexicon in self.EVENT_LEXICONS.items():
            score = 0.0
            matches = []
            for kw, weight in lexicon.items():
                # Word boundary search
                pattern = r"\b" + re.escape(kw) + r"\b"
                found = len(re.findall(pattern, combined_text))
                if found > 0:
                    score += weight * min(found, 3)  # Cap repetitions
                    matches.append(kw)

            if score > 0:
                scores[event_type] = score
                matched_keywords[event_type] = matches

        if not scores:
            return EventClassificationResult(
                primary_event=FinancialEventType.GENERAL_MARKET,
                confidence=0.50,
                secondary_events=(),
                trigger_keywords=(),
                surveillance_relevance=0.15
            )

        # Sort categories by score descending
        sorted_events = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        primary_event, top_score = sorted_events[0]

        # Calculate normalized confidence bounded [0.55, 0.98]
        confidence = min(0.98, 0.55 + (top_score * 0.10))

        secondary = tuple(ev for ev, sc in sorted_events[1:3] if sc >= 1.0)
        triggers = tuple(matched_keywords[primary_event])

        relevance = round(
            min(1.0, self.SURVEILLANCE_MULTIPLIERS.get(primary_event, 0.20) * (confidence / 0.80)),
            2
        )

        return EventClassificationResult(
            primary_event=primary_event,
            confidence=round(confidence, 3),
            secondary_events=secondary,
            trigger_keywords=triggers,
            surveillance_relevance=relevance
        )
