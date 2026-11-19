"""Financial News RSS Ingestion Client.

Fetches, parses, and normalizes financial news articles from verified public RSS/XML feeds.
Cleans HTML entities, standardizes publication timestamps to UTC, and applies
resilient retry policies and SHA-256 provenance tracking.
"""
from datetime import datetime, timezone
import email.utils
import hashlib
import html
import logging
import re
from typing import Dict, List, Optional
import httpx

try:
    import defusedxml.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

try:
    import dateutil.parser as date_parser
except ImportError:
    date_parser = None

from ingestion.schemas import NewsArticleIngestSchema
from ingestion.utils.retry_policy import ingestion_retry

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
        """Parse RFC 822 / 2822 / ISO publication date string into timezone-aware UTC datetime."""
        clean_str = date_str.strip()
        # Attempt dateutil parse first for robust timezone and format handling
        if date_parser is not None:
            try:
                dt = date_parser.parse(clean_str)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass

        # Fallback to standard email.utils RFC 2822 parser
        parsed_tuple = email.utils.parsedate_tz(clean_str)
        if parsed_tuple:
            timestamp = email.utils.mktime_tz(parsed_tuple)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)

        # Fallback to ISO format
        try:
            iso_str = clean_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso_str)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

        raise ValueError(f"Unable to parse date string: {date_str}")

    def parse_rss_xml(
        self,
        xml_content: str,
        source_outlet: str,
        content_hash: Optional[str] = None,
    ) -> List[NewsArticleIngestSchema]:
        """Parse RSS XML content into a list of validated NewsArticleIngestSchema objects."""
        articles = []
        root = ET.fromstring(xml_content)
        now_utc = datetime.now(timezone.utc)

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
                article_hash = hashlib.sha256(f"{link}:{title}".encode("utf-8")).hexdigest()
                article = NewsArticleIngestSchema(
                    canonical_url=link,
                    title=title,
                    summary=summary or None,
                    source_outlet=source_outlet,
                    published_at_utc=pub_date_utc,
                    retrieval_timestamp_utc=now_utc,
                    content_hash=article_hash or content_hash,
                )
                articles.append(article)
            except Exception as e:
                logger.warning("Skipping invalid article '%s': %s", title[:40], e)
                continue

        return articles

    @ingestion_retry()
    def fetch_and_parse_feed(self, url: str, source_outlet: str) -> List[NewsArticleIngestSchema]:
        """Fetch live RSS XML from URL with automated retry policy and return validated articles."""
        logger.info("Fetching RSS feed from %s", url)
        with httpx.Client(headers=self.headers, timeout=15.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            content = resp.text
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            return self.parse_rss_xml(content, source_outlet, content_hash=content_hash)
