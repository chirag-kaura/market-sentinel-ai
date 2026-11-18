"""NSE Delivery Position Report Client.

Downloads and parses official daily security-wise delivery position reports (MTO)
published by the National Stock Exchange of India (NSE).
"""
import io
import logging
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
import urllib.request

logger = logging.getLogger(__name__)


class NSEDeliveryClient:
    """Client for downloading and parsing NSE daily delivery (MTO) reports."""

    def __init__(self, user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"):
        self.user_agent = user_agent
        self.base_headers = {
            "User-Agent": self.user_agent,
            "Accept": "*/*",
            "Referer": "https://www.nseindia.com/all-reports",
        }

    def construct_mto_url(self, trade_date: date) -> str:
        """Construct official NSE MTO delivery report download URL."""
        date_str = trade_date.strftime("%d%m%Y")
        return f"https://nsearchives.nseindia.com/archives/equities/mto/MTO_{date_str}.DAT"

    def parse_mto_stream(self, text_stream: io.TextIOBase) -> Dict[str, Dict]:
        """Parse MTO dat stream and return a dictionary keyed by equity symbol.

        MTO layout format:
        Record Type 20: 20, <SrNo>, <Symbol>, <Series>, <TradedQty>, <DeliverableQty>, <DeliveryPct>
        """
        delivery_map = {}
        for line in text_stream:
            line_str = line.strip()
            if not line_str or line_str.startswith("10") or line_str.startswith("99"):
                # Header (10) or Trailer (99) lines
                continue

            parts = [p.strip() for p in line_str.split(",")]
            if len(parts) >= 7 and parts[0] == "20":
                series = parts[3]
                if series != "EQ":
                    continue
                symbol = parts[2]
                try:
                    traded_qty = int(parts[4])
                    delivery_qty = int(parts[5])
                    delivery_pct = Decimal(parts[6])

                    delivery_map[symbol] = {
                        "symbol": symbol,
                        "traded_qty": traded_qty,
                        "delivery_qty": delivery_qty,
                        "delivery_pct": delivery_pct,
                    }
                except Exception as e:
                    logger.warning("Error parsing MTO line for symbol %s: %s", symbol, e)
                    continue

        return delivery_map
