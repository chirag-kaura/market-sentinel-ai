"""Unit tests for Market Data Ingestion and Validation Pipeline."""
import io
from decimal import Decimal
import os
import pytest

from ingestion.market.nse_bhavcopy_client import NSEBhavcopyClient
from ingestion.market.nse_delivery_client import NSEDeliveryClient
from ingestion.market.market_normalizer import MarketDataNormalizer
from ingestion.schemas import MarketQuoteIngestSchema

# Realistic official UDiFF sample data
SAMPLE_UDIFF_CSV = """TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,ChngInOpnIntrst,TtlTradgVol,TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd01,Rsvd02,Rsvd03,Rsvd04
2026-11-17,2026-11-17,CM,NSE,STK,1001,INE002A01018,RELIANCE,EQ,,,,,,2450.00,2485.50,2440.00,2475.25,2474.00,2445.00,,,0,0,5234120,12950000000.00,142500,1,1,,,,
2026-11-17,2026-11-17,CM,NSE,STK,1002,INE467B01029,TCS,EQ,,,,,,4120.00,4150.00,4090.00,4135.00,4130.00,4110.00,,,0,0,2140500,8850000000.00,98500,1,1,,,,
2026-11-17,2026-11-17,CM,NSE,STK,1003,INE009A01021,INFY,EQ,,,,,,1850.00,1875.00,1830.00,1865.00,1860.00,1845.00,,,0,0,3450000,6420000000.00,82000,1,1,,,,
2026-11-17,2026-11-17,CM,NSE,BOND,2001,INE999A01001,GOVTBOND,GS,,,,,,100.00,100.50,99.80,100.10,100.10,100.00,,,0,0,50000,5005000.00,120,1,1,,,,
"""

# Realistic official MTO sample data
SAMPLE_MTO_DAT = """10,SECURITY WISE DELIVERABLE POSITION FOR 17/11/2026
20,1,RELIANCE,EQ,5234120,2850000,54.45
20,2,TCS,EQ,2140500,1320000,61.67
20,3,INFY,EQ,3450000,1950000,56.52
20,4,GOVTBOND,GS,50000,45000,90.00
99,TOTAL RECORDS: 4
"""


def test_bhavcopy_client_parsing():
    """Test parsing of uncompressed UDiFF Bhavcopy stream."""
    client = NSEBhavcopyClient()
    stream = io.StringIO(SAMPLE_UDIFF_CSV)
    records = client.parse_csv_stream(stream)

    assert len(records) == 3  # Strictly filtered series == 'EQ'
    assert records[0]["symbol"] == "RELIANCE"
    assert records[0]["open_price"] == Decimal("2450.00")
    assert records[0]["high_price"] == Decimal("2485.50")
    assert records[0]["close_price"] == Decimal("2475.25")
    assert records[0]["volume"] == 5234120


def test_delivery_client_parsing():
    """Test parsing of NSE MTO delivery report."""
    client = NSEDeliveryClient()
    stream = io.StringIO(SAMPLE_MTO_DAT)
    delivery_map = client.parse_mto_stream(stream)

    assert len(delivery_map) == 3  # Only EQ series
    assert "RELIANCE" in delivery_map
    assert delivery_map["RELIANCE"]["delivery_qty"] == 2850000
    assert delivery_map["RELIANCE"]["delivery_pct"] == Decimal("54.45")


def test_market_data_normalizer_valid_merge():
    """Test merging and schema validation for valid authentic records."""
    bhavcopy_client = NSEBhavcopyClient()
    delivery_client = NSEDeliveryClient()
    normalizer = MarketDataNormalizer(
        monitored_symbols={"RELIANCE", "TCS", "INFY"},
        quarantine_file="data/quarantine/test_quarantine.jsonl"
    )

    bhav_records = bhavcopy_client.parse_csv_stream(io.StringIO(SAMPLE_UDIFF_CSV))
    deliv_records = delivery_client.parse_mto_stream(io.StringIO(SAMPLE_MTO_DAT))

    valid, quarantined = normalizer.merge_and_validate(bhav_records, deliv_records)

    assert len(valid) == 3
    assert len(quarantined) == 0

    rel = next(r for r in valid if r.symbol == "RELIANCE")
    assert isinstance(rel, MarketQuoteIngestSchema)
    assert rel.close_price == Decimal("2475.25")
    assert rel.delivery_qty == 2850000
    assert rel.delivery_pct == Decimal("54.45")


def test_market_data_normalizer_quarantines_invalid_record():
    """Test quarantine routing for corrupted high/low inverted records."""
    normalizer = MarketDataNormalizer(
        monitored_symbols={"BADSYM"},
        quarantine_file="data/quarantine/test_quarantine.jsonl"
    )

    corrupted_bhav = [
        {
            "symbol": "BADSYM",
            "trade_date": "2026-11-17",
            "open_price": Decimal("2400.00"),
            "high_price": Decimal("2350.00"),  # Corrupted: high < open and high < low
            "low_price": Decimal("2450.00"),
            "close_price": Decimal("2410.00"),
            "volume": 100000,
            "turnover": Decimal("240000000.00"),
        }
    ]

    valid, quarantined = normalizer.merge_and_validate(corrupted_bhav, {})

    assert len(valid) == 0
    assert len(quarantined) == 1
    assert os.path.exists("data/quarantine/test_quarantine.jsonl")

    # Clean up test artifact
    if os.path.exists("data/quarantine/test_quarantine.jsonl"):
        os.remove("data/quarantine/test_quarantine.jsonl")
