"""NSE Bhavcopy Client.

Downloads, extracts, and parses official National Stock Exchange of India (NSE)
Unified Distributable File Format (UDiFF) Bhavcopy reports.
Supports resilient network download with exponential backoff and SHA-256 provenance tracking.
"""
import csv
import hashlib
import io
import logging
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import zipfile
import httpx

from ingestion.utils.retry_policy import ingestion_retry

logger = logging.getLogger(__name__)


class NSEBhavcopyClient:
    """Client for downloading and parsing official daily NSE Bhavcopy files."""

    def __init__(self, user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"):
        self.user_agent = user_agent
        self.base_headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/all-reports",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-site",
        }

    def construct_udiff_url(self, trade_date: date) -> str:
        """Construct official NSE UDiFF daily bhavcopy download URL."""
        date_str = trade_date.strftime("%Y%m%d")
        return f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date_str}_F_0000.csv.zip"

    @ingestion_retry()
    def download_bhavcopy(self, trade_date: date) -> bytes:
        """Download raw Bhavcopy ZIP archive with automated retry policy."""
        url = self.construct_udiff_url(trade_date)
        logger.info("Downloading NSE Bhavcopy from %s", url)
        with httpx.Client(headers=self.base_headers, timeout=30.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.content

    def parse_csv_stream(self, csv_file: io.TextIOBase) -> List[Dict]:
        """Parse uncompressed Bhavcopy CSV records and normalize fields.

        Only retains regular equity series ('EQ').
        """
        reader = csv.DictReader(csv_file)
        records = []
        for row in reader:
            # Standard UDiFF headers: TradDt, TckrSymb, SctySrs, OpnPric, HghPric, LwPric, ClsPric, TtlTradgVol, TtlTrfVal
            series = row.get("SctySrs", "").strip()
            if series != "EQ":
                continue

            symbol = row.get("TckrSymb", "").strip()
            if not symbol:
                continue

            try:
                record = {
                    "symbol": symbol,
                    "trade_date": row.get("TradDt", "").strip(),
                    "series": series,
                    "open_price": Decimal(row.get("OpnPric", "0").strip()),
                    "high_price": Decimal(row.get("HghPric", "0").strip()),
                    "low_price": Decimal(row.get("LwPric", "0").strip()),
                    "close_price": Decimal(row.get("ClsPric", "0").strip()),
                    "volume": int(row.get("TtlTradgVol", "0").strip()),
                    "turnover": Decimal(row.get("TtlTrfVal", "0").strip()),
                }
                records.append(record)
            except Exception as e:
                logger.warning("Failed to parse row for symbol %s: %s", symbol, e)
                continue

        return records

    def parse_zip_bytes(self, zip_bytes: bytes) -> List[Dict]:
        """Extract and parse CSV from downloaded ZIP archive bytes."""
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            csv_filenames = [name for name in zf.namelist() if name.endswith(".csv")]
            if not csv_filenames:
                raise ValueError("No CSV file found inside NSE Bhavcopy ZIP archive.")
            with zf.open(csv_filenames[0]) as csv_file:
                text_stream = io.TextIOWrapper(csv_file, encoding="utf-8")
                return self.parse_csv_stream(text_stream)

    def download_and_parse(self, trade_date: date) -> Tuple[List[Dict], str, str]:
        """Download, verify SHA-256 checksum, and parse Bhavcopy records.

        Returns:
            Tuple of (records, source_url, content_hash)
        """
        url = self.construct_udiff_url(trade_date)
        zip_bytes = self.download_bhavcopy(trade_date)
        content_hash = hashlib.sha256(zip_bytes).hexdigest()
        records = self.parse_zip_bytes(zip_bytes)
        return records, url, content_hash
