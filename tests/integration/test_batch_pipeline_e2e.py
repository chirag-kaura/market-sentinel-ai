"""End-to-End Integration Test for Batch Data Ingestion and Persistence Pipeline.

Validates the complete execution loop:
Raw Exchange Reports -> Parsing -> Pydantic Validation -> Data Cleaning ->
Columnar Parquet Feature Storage -> News RSS Ingestion -> Deduplication -> Audit Trails.
"""
import io
import os
import pandas as pd
import pytest

from ingestion.market.nse_bhavcopy_client import NSEBhavcopyClient
from ingestion.market.nse_delivery_client import NSEDeliveryClient
from ingestion.market.market_normalizer import MarketDataNormalizer
from processing.pandas.market_cleaner import MarketDataCleaner
from processing.pandas.parquet_storage import ParquetStorage
from ingestion.news.rss_news_client import RSSNewsClient
from processing.pandas.news_deduplicator import NewsDeduplicator

SAMPLE_BHAVCOPY_CSV = """TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,ChngInOpnIntrst,TtlTradgVol,TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd01,Rsvd02,Rsvd03,Rsvd04
2026-11-17,2026-11-17,CM,NSE,STK,1001,INE002A01018,RELIANCE,EQ,,,,,,2450.00,2485.50,2440.00,2475.25,2474.00,2445.00,,,0,0,5234120,12950000000.00,142500,1,1,,,,
2026-11-17,2026-11-17,CM,NSE,STK,1002,INE467B01029,TCS,EQ,,,,,,4120.00,4150.00,4090.00,4135.00,4130.00,4110.00,,,0,0,2140500,8850000000.00,98500,1,1,,,,
2026-11-17,2026-11-17,CM,NSE,STK,1003,INE009A01021,INFY,EQ,,,,,,1850.00,1875.00,1830.00,1865.00,1860.00,1845.00,,,0,0,3450000,6420000000.00,82000,1,1,,,,
"""

SAMPLE_DELIVERY_DAT = """10,SECURITY WISE DELIVERABLE POSITION FOR 17/11/2026
20,1,RELIANCE,EQ,5234120,2850000,54.45
20,2,TCS,EQ,2140500,1320000,61.67
20,3,INFY,EQ,3450000,1950000,56.52
99,TOTAL RECORDS: 3
"""

SAMPLE_NEWS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Financial Express - Market News</title>
    <link>https://financialexpress.com</link>
    <item>
      <title>Sensex, Nifty rally as Reliance and IT majors post robust volume gains</title>
      <link>https://financialexpress.com/market/sensex-rally-17112026?utm_source=rss</link>
      <description><![CDATA[<p>Indian benchmark indices surged on Tuesday led by heavy buying in Reliance and TCS.</p>]]></description>
      <pubDate>Tue, 17 Nov 2026 09:30:00 +0530</pubDate>
    </item>
    <item>
      <title>Sensex, Nifty rally as Reliance and IT majors post robust volume gains!</title>
      <link>https://financialexpress.com/market/sensex-rally-17112026?utm_source=twitter</link>
      <description>Syndicated duplicate copy.</description>
      <pubDate>Tue, 17 Nov 2026 09:30:00 +0530</pubDate>
    </item>
  </channel>
</rss>
"""


def test_batch_pipeline_end_to_end(tmp_path):
    """Test full integration from raw exchange streams to clean Parquet feature storage and news deduplication."""
    # 1. Parse raw market feeds
    bhav_client = NSEBhavcopyClient()
    deliv_client = NSEDeliveryClient()

    bhav_records = bhav_client.parse_csv_stream(io.StringIO(SAMPLE_BHAVCOPY_CSV))
    deliv_map = deliv_client.parse_mto_stream(io.StringIO(SAMPLE_DELIVERY_DAT))

    assert len(bhav_records) == 3
    assert len(deliv_map) == 3

    # 2. Normalize and validate via Pydantic
    quarantine_path = str(tmp_path / "quarantine.jsonl")
    normalizer = MarketDataNormalizer(
        monitored_symbols={"RELIANCE", "TCS", "INFY"},
        quarantine_file=quarantine_path
    )
    valid_quotes, quarantined = normalizer.merge_and_validate(bhav_records, deliv_map)

    assert len(valid_quotes) == 3
    assert len(quarantined) == 0

    # 3. Clean and verify DataFrames
    raw_dicts = [q.model_dump() for q in valid_quotes]
    clean_df, audit_metrics = MarketDataCleaner.clean_quotes(raw_dicts)

    assert audit_metrics["final_clean_rows"] == 3
    assert audit_metrics["duplicates_removed"] == 0
    assert audit_metrics["corrupted_rows_quarantined"] == 0

    # 4. Persist to columnar Parquet store with symbol partitioning
    features_dir = str(tmp_path / "features")
    storage = ParquetStorage(base_dir=features_dir)
    target_path = storage.write_features_dataframe(
        clean_df, dataset_name="market_quotes", partition_by_symbol=True
    )

    assert os.path.exists(target_path)
    assert os.path.exists(os.path.join(target_path, "symbol=RELIANCE"))
    assert os.path.exists(os.path.join(target_path, "symbol=TCS"))
    assert os.path.exists(os.path.join(target_path, "symbol=INFY"))

    # 5. Read back from Parquet and verify data fidelity
    reloaded_df = storage.read_features(dataset_name="market_quotes", symbols=["RELIANCE"])
    assert len(reloaded_df) == 1
    rel_row = reloaded_df.iloc[0]
    assert rel_row["symbol"] == "RELIANCE"
    assert rel_row["close_price"] == 2475.25
    assert rel_row["delivery_qty"] == 2850000
    assert rel_row["delivery_pct"] == 54.45

    # 6. Test News Pipeline & Deduplication
    news_client = RSSNewsClient()
    parsed_articles = news_client.parse_rss_xml(SAMPLE_NEWS_XML, source_outlet="Financial Express")
    assert len(parsed_articles) == 2

    raw_news_dicts = [a.model_dump() for a in parsed_articles]
    unique_news, dup_news, dedup_metrics = NewsDeduplicator.deduplicate_articles(raw_news_dicts)

    assert dedup_metrics["total_input"] == 2
    assert dedup_metrics["retained_unique"] == 1
    assert dedup_metrics["exact_url_duplicates"] == 1
    assert len(unique_news) == 1
    assert "<p>" not in unique_news[0]["summary"]
