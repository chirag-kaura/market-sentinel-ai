"""Market Data Repository.

Handles database operations and idempotent upserts for market quotes and symbol master records.
"""
from datetime import date
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.models.market import MarketQuoteModel, SymbolMasterModel


class MarketRepository:
    """Repository handling database access for market entities."""

    def __init__(self, session: Session):
        self.session = session

    def upsert_quotes(self, quotes_data: List[Dict]) -> int:
        """Idempotently upsert market quote records using PostgreSQL ON CONFLICT DO UPDATE.

        Matches on unique constraint: (symbol, trade_date).
        Returns number of inserted/updated rows.
        """
        if not quotes_data:
            return 0

        stmt = insert(MarketQuoteModel).values(quotes_data)
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uq_market_quotes_symbol_date",
            set_={
                "open_price": stmt.excluded.open_price,
                "high_price": stmt.excluded.high_price,
                "low_price": stmt.excluded.low_price,
                "close_price": stmt.excluded.close_price,
                "volume": stmt.excluded.volume,
                "turnover": stmt.excluded.turnover,
                "delivery_qty": stmt.excluded.delivery_qty,
                "delivery_pct": stmt.excluded.delivery_pct,
                "source_provider": stmt.excluded.source_provider,
                "ingested_at_utc": stmt.excluded.ingested_at_utc,
            },
        )
        result = self.session.execute(upsert_stmt)
        self.session.commit()
        return result.rowcount

    def get_quotes_by_symbol(
        self, symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[MarketQuoteModel]:
        """Query chronological quotes for a symbol with optional date range filters."""
        query = select(MarketQuoteModel).where(MarketQuoteModel.symbol == symbol)
        if start_date:
            query = query.where(MarketQuoteModel.trade_date >= start_date)
        if end_date:
            query = query.where(MarketQuoteModel.trade_date <= end_date)
        query = query.order_by(MarketQuoteModel.trade_date.asc())

        return list(self.session.scalars(query).all())
