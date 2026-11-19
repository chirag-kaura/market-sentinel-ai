"""SQLAlchemy ORM models for Market Sentinel AI database tables."""
from datetime import date, datetime
from decimal import Decimal
import uuid
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class SymbolMasterModel(Base):
    """SQLAlchemy ORM model for canonical symbol master reference."""
    __tablename__ = "symbol_master"

    symbol = Column(String(20), primary_key=True)
    company_name = Column(String(255), nullable=False)
    isin = Column(String(12), nullable=False, unique=True, index=True)
    sector = Column(String(100), nullable=False, index=True)
    industry = Column(String(150), nullable=False)
    exchange = Column(String(10), nullable=False, default="NSE")
    series = Column(String(5), nullable=False, default="EQ")
    listing_date = Column(Date, nullable=False)
    market_cap_tier = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    aliases = Column(JSONB().with_variant(JSON(), "sqlite"), nullable=False, default=list)
    created_at_utc = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at_utc = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    quotes = relationship("MarketQuoteModel", back_populates="symbol_ref", cascade="all, delete-orphan")


class MarketQuoteModel(Base):
    """SQLAlchemy ORM model for authentic daily OHLCV and delivery quotes."""
    __tablename__ = "market_quotes_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), ForeignKey("symbol_master.symbol", ondelete="CASCADE"), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    open_price = Column(Numeric(12, 2), nullable=False)
    high_price = Column(Numeric(12, 2), nullable=False)
    low_price = Column(Numeric(12, 2), nullable=False)
    close_price = Column(Numeric(12, 2), nullable=False)
    volume = Column(BigInteger, nullable=False)
    turnover = Column(Numeric(18, 2), nullable=False)
    delivery_qty = Column(BigInteger, nullable=True)
    delivery_pct = Column(Numeric(6, 2), nullable=True)
    source_provider = Column(String(50), nullable=False)
    retrieval_timestamp_utc = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=True)
    original_source_url = Column(String(1000), nullable=True)
    content_hash = Column(String(64), nullable=True)
    ingested_at_utc = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    symbol_ref = relationship("SymbolMasterModel", back_populates="quotes")

    __table_args__ = (
        UniqueConstraint("symbol", "trade_date", name="uq_market_quotes_symbol_date"),
        CheckConstraint("open_price > 0", name="chk_open_positive"),
        CheckConstraint("high_price >= low_price", name="chk_high_low_valid"),
        CheckConstraint("high_price >= open_price", name="chk_high_open_valid"),
        CheckConstraint("high_price >= close_price", name="chk_high_close_valid"),
        CheckConstraint("low_price > 0", name="chk_low_positive"),
        CheckConstraint("close_price > 0", name="chk_close_positive"),
        CheckConstraint("volume >= 0", name="chk_volume_non_negative"),
    )


class RiskAlertModel(Base):
    """SQLAlchemy ORM model for surveillance risk alerts (table: risk_alerts)."""
    __tablename__ = "risk_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(20), ForeignKey("symbol_master.symbol", ondelete="CASCADE"), nullable=False, index=True)
    alert_date = Column(Date, nullable=False, index=True)
    risk_score = Column(Numeric(5, 2), nullable=False)
    priority_tier = Column(String(20), nullable=False, index=True)
    alert_category = Column(String(50), nullable=False)
    summary_explanation = Column(Text, nullable=True)
    abnormal_return = Column(Numeric(8, 4), nullable=True)
    volume_ratio = Column(Numeric(8, 2), nullable=True)
    sentiment_score = Column(Numeric(5, 2), nullable=True)
    novelty_score = Column(Numeric(5, 2), nullable=True)
    has_matching_news = Column(Boolean, default=False, nullable=False)
    dossier_status = Column(String(30), default="PENDING", nullable=False)
    review_status = Column(String(30), default="UNREVIEWED", nullable=False)
    citations = Column(JSONB().with_variant(JSON(), "sqlite"), nullable=False, default=list)
    model_version = Column(String(50), default="1.0.0", nullable=False)
    created_at_utc = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class CorporateAnnouncementModel(Base):
    """SQLAlchemy ORM model for corporate announcements (table: corporate_announcements)."""
    __tablename__ = "corporate_announcements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(20), ForeignKey("symbol_master.symbol", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    body_text = Column(Text, nullable=True)
    attachment_url = Column(String(1000), nullable=True)
    published_at_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    source_provider = Column(String(50), nullable=False)
    retrieval_timestamp_utc = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=True)
    original_source_url = Column(String(1000), nullable=True)
    content_hash = Column(String(64), nullable=True)
    ingested_at_utc = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class NewsArticleModel(Base):
    """SQLAlchemy ORM model for public financial news (table: news_articles)."""
    __tablename__ = "news_articles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_url = Column(String(1000), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    source_outlet = Column(String(100), nullable=False, index=True)
    published_at_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    sentiment_score = Column(Numeric(4, 3), nullable=True)
    retrieval_timestamp_utc = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=True)
    content_hash = Column(String(64), nullable=True)
    ingested_at_utc = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class MarketFeatureDailyModel(Base):
    """SQLAlchemy ORM model for daily market features (table: market_features_daily)."""
    __tablename__ = "market_features_daily"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(20), ForeignKey("symbol_master.symbol", ondelete="CASCADE"), nullable=False, index=True)
    feature_date = Column(Date, nullable=False, index=True)
    return_daily = Column(Numeric(10, 6), nullable=False)
    return_log = Column(Numeric(10, 6), nullable=False)
    return_roll_20d = Column(Numeric(10, 6), nullable=False)
    volatility_roll_20d = Column(Numeric(10, 6), nullable=False)
    volume_ratio_20d = Column(Numeric(10, 4), nullable=False)
    volume_zscore_20d = Column(Numeric(8, 4), nullable=False)
    price_gap = Column(Numeric(10, 6), nullable=False, default=0.0)
    delivery_zscore_20d = Column(Numeric(8, 4), nullable=True)
    is_circuit_locked = Column(Boolean, default=False, nullable=False)
    created_at_utc = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "feature_date", name="uq_mkt_features_symbol_date"),
    )
