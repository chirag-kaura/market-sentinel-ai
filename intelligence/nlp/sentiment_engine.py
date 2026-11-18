"""
Contextual Financial Sentiment Analysis Engine.
Phase 7 — Step 7.5: Computes domain-adapted financial sentiment scores
(Loughran-McDonald inspired polarities, certainty vs uncertainty, and polarity bounds).
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Dict, List, Optional, Set, Tuple


class SentimentPolarity(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


@dataclass(frozen=True)
class FinancialSentimentResult:
    """Structured financial sentiment analysis score and polarity metadata."""
    compound_score: float  # Scale [-1.0, 1.0]
    polarity: SentimentPolarity
    pos_score: float
    neu_score: float
    neg_score: float
    uncertainty_score: float  # Scale [0.0, 1.0]
    top_positive_words: Tuple[str, ...]
    top_negative_words: Tuple[str, ...]


class FinancialSentimentEngine:
    """
    Financial sentiment scoring engine adapted from Loughran-McDonald financial dictionary
    conventions. Avoids misleading colloquial sentiment (e.g. 'crush', 'beat', 'cut')
    and provides explicit uncertainty quantification.
    """

    # Domain-adapted financial positive words
    FINANCIAL_POSITIVE: Dict[str, float] = {
        "profit": 1.2, "growth": 1.1, "surge": 1.3, "surges": 1.3, "record": 1.2,
        "beat": 1.4, "beats": 1.4, "exceed": 1.2, "exceeded": 1.3, "outperform": 1.4,
        "upgrade": 1.3, "upgrades": 1.3, "gain": 1.0, "gains": 1.0, "rally": 1.2,
        "dividend": 1.1, "expansion": 1.0, "strong": 1.0, "bullish": 1.3, "robust": 1.1,
        "soars": 1.3, "jump": 1.1, "jumps": 1.1, "high": 0.8, "higher": 0.9,
        "acquisition": 1.2, "deal": 1.0, "contract": 1.1, "bags": 1.1, "mega": 1.0,
        "transformation": 1.0, "major": 0.8
    }

    # Domain-adapted financial negative words
    FINANCIAL_NEGATIVE: Dict[str, float] = {
        "loss": 1.3, "losses": 1.4, "decline": 1.1, "declines": 1.1, "drop": 1.1,
        "slump": 1.3, "slumps": 1.3, "miss": 1.2, "misses": 1.3, "downgrade": 1.4,
        "downgrades": 1.4, "penalty": 1.5, "fine": 1.2, "fraud": 2.0, "probe": 1.5,
        "investigation": 1.4, "scam": 1.8, "raid": 1.5, "deficit": 1.2, "crash": 1.5,
        "bearish": 1.2, "weak": 1.1, "weakness": 1.1, "default": 1.8, "bankruptcy": 2.0,
        "down": 0.8, "lower": 0.9, "fall": 1.0, "falls": 1.0,
        "inquiry": 1.4, "manipulation": 1.8, "alleged": 1.2, "insider": 1.5, "audit": 1.2
    }

    # Financial uncertainty / ambiguity words
    UNCERTAINTY_WORDS: Set[str] = {
        "uncertain", "uncertainty", "speculation", "volatile", "volatility",
        "pending", "unclear", "contingent", "approximate", "unconfirmed",
        "rumor", "rumours", "maybe", "possible", "potential"
    }

    # Negation words flipping subsequent polarity
    NEGATION_WORDS: Set[str] = {
        "not", "no", "never", "without", "hardly", "barely", "fails", "failed", "neither"
    }

    def __init__(self, neutral_window: float = 0.15):
        self.neutral_window = neutral_window

    def analyze(self, text: str, headline: Optional[str] = None) -> FinancialSentimentResult:
        """Computes financial sentiment, compound polarity, and uncertainty score."""
        combined = f"{headline or ''} {text}".lower()
        words = re.findall(r"\b\w+\b", combined)

        if not words:
            return FinancialSentimentResult(
                compound_score=0.0,
                polarity=SentimentPolarity.NEUTRAL,
                pos_score=0.0,
                neu_score=1.0,
                neg_score=0.0,
                uncertainty_score=0.0,
                top_positive_words=(),
                top_negative_words=()
            )

        pos_sum = 0.0
        neg_sum = 0.0
        uncertainty_count = 0
        pos_words_found: List[str] = []
        neg_words_found: List[str] = []

        is_negated = False
        negation_distance = 0

        for w in words:
            if w in self.NEGATION_WORDS:
                is_negated = True
                negation_distance = 0
                continue

            if is_negated:
                negation_distance += 1
                if negation_distance > 3:  # Negation scope expires after 3 words
                    is_negated = False

            if w in self.UNCERTAINTY_WORDS:
                uncertainty_count += 1

            if w in self.FINANCIAL_POSITIVE:
                weight = self.FINANCIAL_POSITIVE[w]
                if is_negated:
                    neg_sum += weight
                    neg_words_found.append(f"not_{w}")
                else:
                    pos_sum += weight
                    pos_words_found.append(w)
            elif w in self.FINANCIAL_NEGATIVE:
                weight = self.FINANCIAL_NEGATIVE[w]
                if is_negated:
                    pos_sum += weight
                    pos_words_found.append(f"not_{w}")
                else:
                    neg_sum += weight
                    neg_words_found.append(w)

        total_emotional = pos_sum + neg_sum
        total_tokens = len(words)

        if total_emotional == 0:
            compound = 0.0
            polarity = SentimentPolarity.NEUTRAL
            pos_ratio = 0.0
            neg_ratio = 0.0
            neu_ratio = 1.0
        else:
            # Scaled compound score [-1.0, 1.0]
            compound = (pos_sum - neg_sum) / (total_emotional + 1.0)
            compound = max(-1.0, min(1.0, compound))

            if compound > self.neutral_window:
                polarity = SentimentPolarity.POSITIVE
            elif compound < -self.neutral_window:
                polarity = SentimentPolarity.NEGATIVE
            else:
                polarity = SentimentPolarity.NEUTRAL

            pos_ratio = round(pos_sum / (total_emotional + total_tokens * 0.1), 3)
            neg_ratio = round(neg_sum / (total_emotional + total_tokens * 0.1), 3)
            neu_ratio = max(0.0, round(1.0 - (pos_ratio + neg_ratio), 3))

        uncertainty_ratio = min(1.0, round((uncertainty_count * 2.0) / max(1, total_tokens * 0.15), 3))

        return FinancialSentimentResult(
            compound_score=round(compound, 3),
            polarity=polarity,
            pos_score=pos_ratio,
            neu_score=neu_ratio,
            neg_score=neg_ratio,
            uncertainty_score=uncertainty_ratio,
            top_positive_words=tuple(pos_words_found[:5]),
            top_negative_words=tuple(neg_words_found[:5])
        )
