"""Unit tests for News and Corporate Disclosure Ingestion Clients."""
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import httpx
import pytest

from ingestion.news.rss_news_client import RSSNewsClient
from ingestion.announcements.corporate_disclosure_client import (
    CorporateDisclosureClient,
    CorporateAnnouncementSchema,
)
from ingestion.schemas import NewsArticleIngestSchema

SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Economic Times - Stock News</title>
    <link>https://economictimes.indiatimes.com</link>
    <description>Stock Market News</description>
    <item>
      <title><![CDATA[Tata Motors shares surge 6% on strong JLR global deliveries]]></title>
      <link>https://economictimes.indiatimes.com/markets/stocks/news/tatamotors-jlr-surge/12345.cms</link>
      <description><![CDATA[<p>Tata Motors rallied on Tuesday following robust wholesale deliveries reported across Europe and US markets.</p>]]></description>
      <pubDate>Tue, 17 Nov 2026 10:15:30 +0530</pubDate>
    </item>
    <item>
      <title>Reliance Retail expands omnichannel presence with 50 new stores</title>
      <link>https://economictimes.indiatimes.com/markets/stocks/news/reliance-retail-expansion/67890.cms</link>
      <description>Reliance Industries retail arm announced massive footprint growth.</description>
      <pubDate>Tue, 17 Nov 2026 09:30:00 +0530</pubDate>
    </item>
  </channel>
</rss>
"""

SAMPLE_EXCHANGE_DISCLOSURES = [
    {
        "symbol": "TATAMOTORS",
        "category": "FINANCIAL_RESULTS",
        "subject": "Outcome of Board Meeting for Q2 Results and Dividend Declaration",
        "body_text": "The Board of Directors approved unaudited quarterly financial results with revenue up 18%.",
        "attachment_url": "https://nsearchives.nseindia.com/corporate/TATAMOTORS_17112026.pdf",
        "broadcast_date_time": "2026-11-17 14:45:00",
    },
    {
        "symbol": "INFY",
        "category": "PRESS_RELEASE",
        "subject": "Infosys collaborates with leading European telecom provider for Cloud Transformation",
        "body_text": "Infosys announced a multi-year strategic collaboration today.",
        "attachment_url": None,
        "broadcast_date_time": "2026-11-17 11:20:00",
    }
]

SAMPLE_EDGAR_PAYLOAD = {
    "cik": "0001067983",
    "name": "BERKSHIRE HATHAWAY INC",
    "filings": {
        "recent": {
            "form": ["8-K", "10-Q"],
            "filingDate": ["2026-11-16", "2026-11-10"],
            "acceptanceDateTime": ["2026-11-16T21:15:00.000Z", "2026-11-10T18:30:00.000Z"],
            "accessionNumber": ["0001067983-26-000123", "0001067983-26-000120"],
            "primaryDocument": ["form8k.htm", "form10q.htm"]
        }
    }
}


def test_rss_news_client_parsing():
    """Test RSS XML parsing, text sanitization, and timestamp normalization."""
    client = RSSNewsClient()
    articles = client.parse_rss_xml(SAMPLE_RSS_XML, source_outlet="Economic Times")

    assert len(articles) == 2
    a1 = articles[0]
    assert isinstance(a1, NewsArticleIngestSchema)
    assert a1.title == "Tata Motors shares surge 6% on strong JLR global deliveries"
    assert a1.source_outlet == "Economic Times"
    assert "<p>" not in a1.summary  # Verified HTML stripping
    assert "Tata Motors rallied" in a1.summary
    assert a1.published_at_utc.tzinfo == timezone.utc
    assert a1.published_at_utc.hour == 4  # 10:15 IST minus 5h30m = 04:45 UTC
    assert a1.published_at_utc.minute == 45
    assert a1.retrieval_timestamp_utc is not None
    assert a1.content_hash is not None


def test_corporate_disclosure_client_exchange_ist_conversion():
    """Test parsing exchange corporate announcements with accurate IST to UTC conversion."""
    client = CorporateDisclosureClient()
    announcements = client.parse_exchange_announcements_json(SAMPLE_EXCHANGE_DISCLOSURES)

    assert len(announcements) == 2
    ann1 = announcements[0]
    assert isinstance(ann1, CorporateAnnouncementSchema)
    assert ann1.symbol == "TATAMOTORS"
    assert ann1.category == "FINANCIAL_RESULTS"
    # 14:45 IST converted to UTC is 09:15 UTC (14:45 - 5h30m)
    assert ann1.published_at_utc == datetime(2026, 11, 17, 9, 15, 0, tzinfo=timezone.utc)
    assert ann1.attachment_url == "https://nsearchives.nseindia.com/corporate/TATAMOTORS_17112026.pdf"

    ann2 = announcements[1]
    # 11:20 IST converted to UTC is 05:50 UTC (11:20 - 5h30m)
    assert ann2.published_at_utc == datetime(2026, 11, 17, 5, 50, 0, tzinfo=timezone.utc)


def test_corporate_disclosure_client_edgar():
    """Test parsing SEC EDGAR public submissions API payload."""
    client = CorporateDisclosureClient()
    edgar_announcements = client.parse_sec_edgar_submissions_json(
        SAMPLE_EDGAR_PAYLOAD, target_symbol="BRK.A"
    )

    assert len(edgar_announcements) == 2
    e1 = edgar_announcements[0]
    assert isinstance(e1, CorporateAnnouncementSchema)
    assert e1.symbol == "BRK.A"
    assert e1.category == "SEC_8-K"
    assert e1.published_at_utc == datetime(2026, 11, 16, 21, 15, 0, tzinfo=timezone.utc)
    assert "https://www.sec.gov/Archives/edgar/data/0001067983" in e1.attachment_url


def test_corporate_disclosure_http_fetch_with_mock():
    """Test fetch_exchange_announcements performs HTTP GET and records provenance."""
    client = CorporateDisclosureClient()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"data": [{"symbol": "RELIANCE", "category": "GENERAL", "subject": "Press Release on AGM", "broadcast_date_time": "2026-11-17 10:00:00"}]}'
    mock_response.json.return_value = {
        "data": [
            {
                "symbol": "RELIANCE",
                "category": "GENERAL",
                "subject": "Press Release on AGM",
                "broadcast_date_time": "2026-11-17 10:00:00",
            }
        ]
    }

    with patch("httpx.Client.get", return_value=mock_response):
        announcements = client.fetch_exchange_announcements("https://example.com/announcements")

    assert len(announcements) == 1
    assert announcements[0].symbol == "RELIANCE"
    assert announcements[0].published_at_utc == datetime(2026, 11, 17, 4, 30, 0, tzinfo=timezone.utc)
    assert announcements[0].original_source_url == "https://example.com/announcements"
    assert announcements[0].content_hash is not None


def test_rss_fetch_with_mock_and_provenance():
    """Test RSS fetch_and_parse_feed with mocked HTTP network response."""
    client = RSSNewsClient()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = SAMPLE_RSS_XML

    with patch("httpx.Client.get", return_value=mock_response):
        articles = client.fetch_and_parse_feed("https://example.com/rss", source_outlet="Test Outlet")

    assert len(articles) == 2
    assert articles[0].content_hash is not None
    assert articles[0].retrieval_timestamp_utc is not None
