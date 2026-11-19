"""Corporate Disclosure and Regulatory Filing Ingestion Client.

Ingests and normalizes official corporate filings and regulatory disclosures from
exchange announcement feeds and SEC EDGAR public submissions APIs.
Supports network download with exponential backoff, SHA-256 provenance tracking,
and accurate IST-to-UTC timestamp conversion for Indian market disclosures.
"""
from datetime import datetime, timezone
import hashlib
import json
import logging
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo
import httpx
from pydantic import BaseModel, Field

from ingestion.utils.retry_policy import ingestion_retry, TokenBucketRateLimiter

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
EDGAR_RATE_LIMITER = TokenBucketRateLimiter(capacity=10.0, refill_rate_per_sec=10.0)


class CorporateAnnouncementSchema(BaseModel):
    """Pydantic validation model for corporate announcements and regulatory filings."""
    symbol: str = Field(..., min_length=1, max_length=20)
    category: str = Field(..., min_length=2, max_length=100)
    subject: str = Field(..., min_length=5, max_length=500)
    body_text: Optional[str] = None
    attachment_url: Optional[str] = None
    published_at_utc: datetime
    source_provider: str = Field(..., min_length=2, max_length=50)
    retrieval_timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    original_source_url: Optional[str] = Field(None, max_length=1000)
    content_hash: Optional[str] = Field(None, max_length=64)


class CorporateDisclosureClient:
    """Client for parsing and downloading exchange corporate announcements and regulatory filings."""

    def __init__(self, user_agent: str = "MarketSentinelAI AdminContact@marketsentinel.local"):
        self.user_agent = user_agent
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/plain, */*",
        }

    def parse_exchange_announcements_json(
        self,
        json_data: List[Dict],
        source_provider: str = "SRC-NSE-CORP-ANNOUNCEMENTS",
        original_source_url: Optional[str] = None,
        content_hash: Optional[str] = None,
    ) -> List[CorporateAnnouncementSchema]:
        """Parse corporate announcement payload from exchange feeds.

        Accurately converts naive Indian Standard Time (IST, UTC+05:30) timestamps to UTC.
        """
        announcements = []
        now_utc = datetime.now(timezone.utc)
        for item in json_data:
            symbol = item.get("symbol", "").strip()
            subject = item.get("subject", "").strip() or item.get("desc", "").strip()
            category = item.get("category", "GENERAL").strip()
            broadcast_str = item.get("broadcast_date_time", "").strip()

            if not symbol or not subject or not broadcast_str:
                continue

            try:
                # If ISO format with timezone/Z
                if "T" in broadcast_str:
                    pub_dt = datetime.fromisoformat(broadcast_str.replace("Z", "+00:00")).astimezone(timezone.utc)
                else:
                    # NSE/BSE exchange announcement timestamps are published in Indian Standard Time (IST)
                    naive_dt = datetime.strptime(broadcast_str, "%Y-%m-%d %H:%M:%S")
                    pub_dt = naive_dt.replace(tzinfo=IST).astimezone(timezone.utc)

                announcement = CorporateAnnouncementSchema(
                    symbol=symbol,
                    category=category,
                    subject=subject,
                    body_text=item.get("body_text"),
                    attachment_url=item.get("attachment_url"),
                    published_at_utc=pub_dt,
                    source_provider=source_provider,
                    retrieval_timestamp_utc=now_utc,
                    original_source_url=original_source_url,
                    content_hash=content_hash,
                )
                announcements.append(announcement)
            except Exception as e:
                logger.warning("Error parsing announcement for %s: %s", symbol, e)
                continue

        return announcements

    def parse_sec_edgar_submissions_json(
        self,
        cik_payload: Dict,
        target_symbol: str,
        source_provider: str = "SRC-SEC-EDGAR",
        original_source_url: Optional[str] = None,
        content_hash: Optional[str] = None,
    ) -> List[CorporateAnnouncementSchema]:
        """Parse SEC EDGAR submissions API JSON payload into CorporateAnnouncementSchema records."""
        filings = cik_payload.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        acceptance_datetimes = filings.get("acceptanceDateTime", [])
        primary_docs = filings.get("primaryDocument", [])
        accession_numbers = filings.get("accessionNumber", [])

        announcements = []
        now_utc = datetime.now(timezone.utc)
        n_items = min(len(forms), len(acceptance_datetimes))

        for i in range(n_items):
            form_type = forms[i]
            acc_dt_str = acceptance_datetimes[i]
            accession = accession_numbers[i].replace("-", "") if i < len(accession_numbers) else ""
            primary_doc = primary_docs[i] if i < len(primary_docs) else ""

            # Standardize subject
            subject = f"SEC Form {form_type} Filing Submission"
            attachment_url = (
                f"https://www.sec.gov/Archives/edgar/data/{cik_payload.get('cik', '')}/{accession}/{primary_doc}"
                if accession and primary_doc else None
            )

            try:
                # EDGAR format: "2026-11-17T01:57:17.000Z"
                pub_dt = datetime.fromisoformat(acc_dt_str.replace("Z", "+00:00")).astimezone(timezone.utc)
                announcement = CorporateAnnouncementSchema(
                    symbol=target_symbol,
                    category=f"SEC_{form_type.replace('/', '_')}",
                    subject=subject,
                    body_text=f"Formal filing of {form_type} by {cik_payload.get('name', target_symbol)}",
                    attachment_url=attachment_url,
                    published_at_utc=pub_dt,
                    source_provider=source_provider,
                    retrieval_timestamp_utc=now_utc,
                    original_source_url=original_source_url,
                    content_hash=content_hash,
                )
                announcements.append(announcement)
            except Exception as e:
                logger.warning("Failed to parse EDGAR item %d: %s", i, e)
                continue

        return announcements

    @ingestion_retry()
    def fetch_exchange_announcements(
        self,
        url: str,
        source_provider: str = "SRC-NSE-CORP-ANNOUNCEMENTS",
    ) -> List[CorporateAnnouncementSchema]:
        """Fetch live announcements from exchange endpoint with automated retry and provenance."""
        logger.info("Fetching corporate announcements from %s", url)
        with httpx.Client(headers=self.headers, timeout=20.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            raw_text = resp.text
            content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
            json_data = resp.json()
            if isinstance(json_data, dict) and "data" in json_data:
                json_data = json_data["data"]
            return self.parse_exchange_announcements_json(
                json_data,
                source_provider=source_provider,
                original_source_url=url,
                content_hash=content_hash,
            )

    @ingestion_retry(rate_limiter=EDGAR_RATE_LIMITER)
    def fetch_sec_edgar_submissions(
        self,
        cik: str,
        target_symbol: str,
        source_provider: str = "SRC-SEC-EDGAR",
    ) -> List[CorporateAnnouncementSchema]:
        """Fetch official submissions JSON from SEC EDGAR for given 10-digit CIK."""
        cik_padded = str(cik).zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        logger.info("Fetching SEC EDGAR filings for CIK %s from %s", cik_padded, url)
        with httpx.Client(headers=self.headers, timeout=20.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            raw_text = resp.text
            content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
            payload = resp.json()
            return self.parse_sec_edgar_submissions_json(
                payload,
                target_symbol=target_symbol,
                source_provider=source_provider,
                original_source_url=url,
                content_hash=content_hash,
            )
