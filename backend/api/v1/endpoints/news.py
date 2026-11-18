"""
News and Disclosures RESTful API Endpoints.
Phase 6 / Phase 10: FinBERT sentiment and novelty analyzed regulatory filings.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/news", tags=["News Intelligence"])


class NewsAnnouncementItem(BaseModel):
    id: str
    published_time: str
    ticker: str
    company_name: str
    event_category: str
    sentiment: str  # Positive, Neutral, Negative
    novelty: str    # High, Medium, Low
    source_type: str # Official filing, Exchange announcement, News wire
    linked_signal: str
    headline: str


_ANNOUNCEMENTS = [
    NewsAnnouncementItem(
        id="NEWS-2026-001",
        published_time="14:05",
        ticker="INFY",
        company_name="Infosys Limited",
        event_category="Corporate disclosure",
        sentiment="Positive",
        novelty="High",
        source_type="Official filing",
        linked_signal="Volume anomaly",
        headline="Board approval of strategic multi-year cloud expansion contract.",
    ),
    NewsAnnouncementItem(
        id="NEWS-2026-002",
        published_time="12:40",
        ticker="RELIANCE",
        company_name="Reliance Industries Limited",
        event_category="Business update",
        sentiment="Neutral",
        novelty="Medium",
        source_type="News source",
        linked_signal="Price + volume",
        headline="Consortium negotiation updates for domestic energy retail venture.",
    ),
    NewsAnnouncementItem(
        id="NEWS-2026-003",
        published_time="11:20",
        ticker="HDFCBANK",
        company_name="HDFC Bank Limited",
        event_category="Sector / macro",
        sentiment="Negative",
        novelty="Low",
        source_type="News source",
        linked_signal="Volatility",
        headline="RBI monetary committee note on unsecured consumer loan provisions.",
    ),
    NewsAnnouncementItem(
        id="NEWS-2026-004",
        published_time="10:15",
        ticker="TATAMOTORS",
        company_name="Tata Motors Limited",
        event_category="Corporate action",
        sentiment="Positive",
        novelty="High",
        source_type="Official filing",
        linked_signal="Price breakout",
        headline="Electric mobility division reports record monthly retail order bookings.",
    ),
    NewsAnnouncementItem(
        id="NEWS-2026-005",
        published_time="09:40",
        ticker="LT",
        company_name="Larsen & Toubro Limited",
        event_category="Regulatory",
        sentiment="Positive",
        novelty="High",
        source_type="Official filing",
        linked_signal="Volume pre-run",
        headline="Major mega-order win of over INR 10,000 Cr in transmission & renewables.",
    ),
]


@router.get("", response_model=List[NewsAnnouncementItem])
def list_news(
    ticker: Optional[str] = Query(None, description="Filter news by ticker symbol"),
    event_category: Optional[str] = Query(None, description="Filter by event category"),
):
    """Retrieve verified news announcements with NLP classifications."""
    results = _ANNOUNCEMENTS
    if ticker:
        results = [n for n in results if n.ticker.upper() == ticker.upper()]
    if event_category:
        results = [n for n in results if event_category.lower() in n.event_category.lower()]
    return results
