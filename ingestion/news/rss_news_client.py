"""Financial News RSS Ingestion Client.

Fetches, parses, and normalizes financial news articles from verified public RSS/XML feeds.
Cleans HTML entities and standardizes publication timestamps to UTC.
"""
from datetime import datetime, timezone
import email.utils
import html
import logging
import re
from typing import Dict, List, Optional
import urllib.request
import xml.etree.ElementTree as ET

from ingestion.schemas import NewsArticleIngestSchema

logger = logging.getLogger(__name__)


class RSSNewsClient:
    """Client for parsing RSS 2.0 and Atom financial news feeds."""

    DEFAULT_FEEDS = {
        "Economic Times - Stocks": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
        "Moneycontrol - Top News": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    }

    def __init__(self, user_agent: str = "MarketSentinelAI/1.0 (+http://localhost:8000)"):
        self.user_agent = user_agent
        self.headers = {"User-Agent": self.user_agent}

    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        """Strip HTML tags, unescape HTML entities, and normalize whitespace."""
        if not text:
            return ""
        # Unescape HTML entities (e.g. &amp;, &quot;)
        clean = html.unescape(text)
        # Remove HTML markup tags
        clean = re.sub(r"<[^>]+>", " ", clean)
        # Collapse multi-spaces
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    @staticmethod
    def parse_rfc822_date(date_str: str) -> datetime:
        """Parse RFC 822 / 2822 publication date string into timezone-aware UTC datetime."""
        parsed_tuple = email.utils.parsedate_tz(date_str)
        if not parsed_tuple:
            raise ValueError(f"Unable to parse date string: {date_str}")
        timestamp = email.utils.mktime_tz(parsed_tuple)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    def parse_rss_xml(self, xml_content: str, source_outlet: str) -> List[NewsArticleIngestSchema]:
        """Parse RSS XML content into a list of validated NewsArticleIngestSchema objects."""
        articles = []
        root = ET.fromstring(xml_content)

        # Standard RSS 2.0 item lookup
        items = root.findall(".//item")
        for item in items:
            title_raw = item.findtext("title", "")
            link_raw = item.findtext("link", "")
            desc_raw = item.findtext("description", "")
            pub_date_raw = item.findtext("pubDate", "")

            title = self.clean_text(title_raw)
            link = link_raw.strip()
            summary = self.clean_text(desc_raw)

            if not title or not link or not pub_date_raw:
                continue

            try:
                pub_date_utc = self.parse_rfc822_date(pub_date_raw)
                article = NewsArticleIngestSchema(
                    canonical_url=link,
                    title=title,
                    summary=summary or None,
                    source_outlet=source_outlet,
                    published_at_utc=pub_date_utc,
                )
                articles.append(article)
            except Exception as e:
                logger.warning("Skipping invalid article '%s': %s", title[:40], e)
                continue

        return articles

    def fetch_and_parse_feed(self, url: str, source_outlet: str) -> List[NewsArticleIngestSchema]:
        """Fetch live RSS XML from URL and return validated articles."""
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            return self.parse_rss_xml(content, source_outlet)
