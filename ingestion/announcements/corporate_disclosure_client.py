"""Corporate Disclosure and Regulatory Filing Ingestion Client.

Ingests and normalizes official corporate filings and regulatory disclosures from
exchange announcement feeds and SEC EDGAR public submissions APIs.
"""
from datetime import datetime, timezone
import json
import logging
from typing import Dict, List, Optional
import urllib.request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CorporateAnnouncementSchema(BaseModel):
    """Pydantic validation model for corporate announcements and regulatory filings."""
    symbol: str = Field(..., min_length=1, max_length=20)
    category: str = Field(..., min_length=2, max_length=100)
    subject: str = Field(..., min_length=5, max_length=500)
    body_text: Optional[str] = None
    attachment_url: Optional[str] = None
    published_at_utc: datetime
    source_provider: str = Field(..., min_length=2, max_length=50)


class CorporateDisclosureClient:
    """Client for parsing exchange corporate announcements and regulatory filings."""

    def __init__(self, user_agent: str = "MarketSentinelAI AdminContact@marketsentinel.local"):
        self.user_agent = user_agent
        self.headers = {"User-Agent": self.user_agent}

    def parse_exchange_announcements_json(
        self,
        json_data: List[Dict],
        source_provider: str = "SRC-NSE-CORP-ANNOUNCEMENTS"
    ) -> List[CorporateAnnouncementSchema]:
        """Parse corporate announcement payload from exchange feeds."""
        announcements = []
        for item in json_data:
            symbol = item.get("symbol", "").strip()
            subject = item.get("subject", "").strip() or item.get("desc", "").strip()
            category = item.get("category", "GENERAL").strip()
            broadcast_str = item.get("broadcast_date_time", "").strip()

            if not symbol or not subject or not broadcast_str:
                continue

            try:
                # Expected format: "2026-11-17 14:30:00" or ISO format
                if "T" in broadcast_str:
                    pub_dt = datetime.fromisoformat(broadcast_str.replace("Z", "+00:00"))
                else:
                    pub_dt = datetime.strptime(broadcast_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

                announcement = CorporateAnnouncementSchema(
                    symbol=symbol,
                    category=category,
                    subject=subject,
                    body_text=item.get("body_text"),
                    attachment_url=item.get("attachment_url"),
                    published_at_utc=pub_dt,
                    source_provider=source_provider,
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
        source_provider: str = "SRC-SEC-EDGAR"
    ) -> List[CorporateAnnouncementSchema]:
        """Parse SEC EDGAR submissions API JSON payload into CorporateAnnouncementSchema records."""
        filings = cik_payload.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        acceptance_datetimes = filings.get("acceptanceDateTime", [])
        primary_docs = filings.get("primaryDocument", [])
        accession_numbers = filings.get("accessionNumber", [])

        announcements = []
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
                pub_dt = datetime.fromisoformat(acc_dt_str.replace("Z", "+00:00"))
                announcement = CorporateAnnouncementSchema(
                    symbol=target_symbol,
                    category=f"SEC_{form_type.replace('/', '_')}",
                    subject=subject,
                    body_text=f"Formal filing of {form_type} by {cik_payload.get('name', target_symbol)}",
                    attachment_url=attachment_url,
                    published_at_utc=pub_dt,
                    source_provider=source_provider,
                )
                announcements.append(announcement)
            except Exception as e:
                logger.warning("Failed to parse EDGAR item %d: %s", i, e)
                continue

        return announcements
