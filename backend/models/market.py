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
