"""Market Data Normalizer and Quality Gate.

Combines parsed Bhavcopy and Delivery records, applies symbol universe filtering,
enforces Pydantic schema validation, and routes invalid records to the quarantine buffer.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
import json
import logging
import os
from typing import Dict, List, Optional, Set, Tuple

from ingestion.schemas import MarketQuoteIngestSchema

logger = logging.getLogger(__name__)


class MarketDataNormalizer:
    """Normalizes and validates market records from raw exchange reports."""

    def __init__(
        self,
        monitored_symbols: Optional[Set[str]] = None,
        quarantine_file: str = "data/quarantine/invalid_records.jsonl",
    ):
        self.monitored_symbols = monitored_symbols
        self.quarantine_file = quarantine_file
        os.makedirs(os.path.dirname(self.quarantine_file), exist_ok=True)

    def quarantine_record(self, raw_data: Dict, error_code: str, error_msg: str) -> None:
        """Route a failed raw payload to the dead-letter quarantine buffer."""
        envelope = {
            "quarantine_id": os.urandom(8).hex(),
            "error_code": error_code,
            "error_message": error_msg,
            "source_provider": raw_data.get("source_provider", "SRC-NSE-EOD"),
            "raw_payload": {
                k: str(v) if isinstance(v, (Decimal, date, datetime)) else v
                for k, v in raw_data.items()
            },
            "quarantined_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.quarantine_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(envelope) + "\n")

    def merge_and_validate(
        self,
        bhavcopy_records: List[Dict],
        delivery_map: Optional[Dict[str, Dict]] = None,
        source_provider: str = "SRC-NSE-EOD",
        original_source_url: Optional[str] = None,
        content_hash: Optional[str] = None,
    ) -> Tuple[List[MarketQuoteIngestSchema], List[Dict]]:
        """Merge Bhavcopy OHLCV with Delivery metrics and validate via Pydantic.

        Returns:
            Tuple of (valid_records, quarantined_records)
        """
        valid_records: List[MarketQuoteIngestSchema] = []
        quarantined_records: List[Dict] = []
        delivery_map = delivery_map or {}
        now_utc = datetime.now(timezone.utc)

        for b_rec in bhavcopy_records:
            symbol = b_rec["symbol"]

            # Filter to monitored universe if configured
            if self.monitored_symbols and symbol not in self.monitored_symbols:
                continue

            deliv_info = delivery_map.get(symbol, {})
            delivery_qty = deliv_info.get("delivery_qty")
            delivery_pct = deliv_info.get("delivery_pct")

            raw_merged = {
                "symbol": symbol,
                "trade_date": b_rec["trade_date"],
                "open_price": b_rec["open_price"],
                "high_price": b_rec["high_price"],
                "low_price": b_rec["low_price"],
                "close_price": b_rec["close_price"],
                "volume": b_rec["volume"],
                "turnover": b_rec["turnover"],
                "delivery_qty": delivery_qty,
                "delivery_pct": delivery_pct,
                "source_provider": source_provider,
                "retrieval_timestamp_utc": now_utc,
                "original_source_url": original_source_url,
                "content_hash": content_hash,
            }

            try:
                # Schema and business rules validation gate
                validated = MarketQuoteIngestSchema(**raw_merged)
                valid_records.append(validated)
            except Exception as e:
                err_code = "ERR_DATA_QUALITY_VALIDATION"
                err_msg = str(e)
                logger.warning("Quarantining record for %s on %s: %s", symbol, b_rec["trade_date"], err_msg)
                self.quarantine_record(raw_merged, err_code, err_msg)
                quarantined_records.append(raw_merged)

        return valid_records, quarantined_records
