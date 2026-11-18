"""Data models and schemas for market data ingestion and quality validation."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class MarketQuoteIngestSchema(BaseModel):
    """Pydantic validation model for raw daily market quotes."""
    symbol: str = Field(..., min_length=1, max_length=20)
    trade_date: date
    open_price: Decimal = Field(..., gt=Decimal("0.0"))
    high_price: Decimal = Field(..., gt=Decimal("0.0"))
    low_price: Decimal = Field(..., gt=Decimal("0.0"))
    close_price: Decimal = Field(..., gt=Decimal("0.0"))
    volume: int = Field(..., ge=0)
    turnover: Decimal = Field(..., ge=Decimal("0.0"))
    delivery_qty: Optional[int] = Field(None, ge=0)
    delivery_pct: Optional[Decimal] = Field(None, ge=Decimal("0.0"), le=Decimal("100.0"))
    source_provider: str = Field(..., min_length=2, max_length=50)

    @model_validator(mode="after")
    def validate_price_boundaries(self) -> "MarketQuoteIngestSchema":
        if self.high_price < self.low_price:
            raise ValueError(
                f"High price ({self.high_price}) cannot be lower than Low price ({self.low_price})"
            )
        if self.high_price < self.open_price or self.high_price < self.close_price:
            raise ValueError(
                f"High price ({self.high_price}) must be >= Open ({self.open_price}) and Close ({self.close_price})"
            )
        if self.low_price > self.open_price or self.low_price > self.close_price:
            raise ValueError(
                f"Low price ({self.low_price}) must be <= Open ({self.open_price}) and Close ({self.close_price})"
            )
        if self.delivery_qty is not None and self.delivery_qty > self.volume:
            raise ValueError(
                f"Delivery quantity ({self.delivery_qty}) cannot exceed total volume ({self.volume})"
            )
        return self


class NewsArticleIngestSchema(BaseModel):
    """Pydantic validation model for raw financial news articles."""
    canonical_url: str = Field(..., min_length=10, max_length=1000)
    title: str = Field(..., min_length=10, max_length=500)
    summary: Optional[str] = None
    body_text: Optional[str] = None
    source_outlet: str = Field(..., min_length=2, max_length=100)
    published_at_utc: datetime

    @model_validator(mode="after")
    def validate_temporal_sanity(self) -> "NewsArticleIngestSchema":
        now_utc = datetime.now(timezone.utc)
        if self.published_at_utc.tzinfo is None:
            raise ValueError("published_at_utc must be timezone-aware (UTC)")
        if (self.published_at_utc - now_utc).total_seconds() > 300:
            raise ValueError(
                f"Publication timestamp ({self.published_at_utc}) is in the future relative to server time ({now_utc})"
            )
        return self
