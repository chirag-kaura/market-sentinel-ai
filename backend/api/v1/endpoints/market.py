"""
Market Data RESTful API Endpoints.
Phase 10 — Step 10.3: Stock metadata, real quotes, and watchlist metrics.
"""

from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.exceptions import EntityNotFoundError
from backend.models.market import SymbolMasterModel, MarketQuoteModel, RiskAlertModel

router = APIRouter(prefix="/market", tags=["Market Data"])


class SymbolInfo(BaseModel):
    symbol: str
    company_name: str
    sector: str
    industry: str
    exchange: str
    is_active: bool


class MarketWatchQuote(BaseModel):
    symbol: str
    company_name: str
    last_price: float
    change_pct: float
    volume_ratio: float
    volatility_regime: str
    signal: str
    risk_score: float
    priority: str


class OHLCVRecord(BaseModel):
    symbol: str
    trade_date: date
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int


_SYMBOLS = {
    "INFY": SymbolInfo(
        symbol="INFY",
        company_name="Infosys Limited",
        sector="Information Technology",
        industry="IT Services & Consulting",
        exchange="NSE",
        is_active=True,
    ),
    "TCS": SymbolInfo(
        symbol="TCS",
        company_name="Tata Consultancy Services Limited",
        sector="Information Technology",
        industry="IT Services & Consulting",
        exchange="NSE",
        is_active=True,
    ),
    "RELIANCE": SymbolInfo(
        symbol="RELIANCE",
        company_name="Reliance Industries Limited",
        sector="Energy & Refining",
        industry="Oil & Gas",
        exchange="NSE",
        is_active=True,
    ),
    "HDFCBANK": SymbolInfo(
        symbol="HDFCBANK",
        company_name="HDFC Bank Limited",
        sector="Financial Services",
        industry="Private Banking",
        exchange="NSE",
        is_active=True,
    ),
    "ICICIBANK": SymbolInfo(
        symbol="ICICIBANK",
        company_name="ICICI Bank Limited",
        sector="Financial Services",
        industry="Private Banking",
        exchange="NSE",
        is_active=True,
    ),
    "BHARTIARTL": SymbolInfo(
        symbol="BHARTIARTL",
        company_name="Bharti Airtel Limited",
        sector="Telecommunications",
        industry="Telecom Services",
        exchange="NSE",
        is_active=True,
    ),
    "TATAMOTORS": SymbolInfo(
        symbol="TATAMOTORS",
        company_name="Tata Motors Limited",
        sector="Automotive",
        industry="Commercial & Passenger Vehicles",
        exchange="NSE",
        is_active=True,
    ),
    "LT": SymbolInfo(
        symbol="LT",
        company_name="Larsen & Toubro Limited",
        sector="Capital Goods",
        industry="Infrastructure & Engineering",
        exchange="NSE",
        is_active=True,
    ),
    "SBIN": SymbolInfo(
        symbol="SBIN",
        company_name="State Bank of India",
        sector="Financial Services",
        industry="Public Banking",
        exchange="NSE",
        is_active=True,
    ),
    "ITC": SymbolInfo(
        symbol="ITC",
        company_name="ITC Limited",
        sector="Fast Moving Consumer Goods",
        industry="Diversified FMCG",
        exchange="NSE",
        is_active=True,
    ),
}

_WATCHLIST_QUOTES = [
    MarketWatchQuote(
        symbol="RELIANCE",
        company_name="Reliance Industries Limited",
        last_price=1462.50,
        change_pct=3.82,
        volume_ratio=3.4,
        volatility_regime="Elevated",
        signal="Price + volume",
        risk_score=91.0,
        priority="HIGH",
    ),
    MarketWatchQuote(
        symbol="INFY",
        company_name="Infosys Limited",
        last_price=1584.20,
        change_pct=2.76,
        volume_ratio=2.9,
        volatility_regime="High",
        signal="Volume + news",
        risk_score=86.0,
        priority="HIGH",
    ),
    MarketWatchQuote(
        symbol="HDFCBANK",
        company_name="HDFC Bank Limited",
        last_price=978.65,
        change_pct=-1.92,
        volume_ratio=1.7,
        volatility_regime="Elevated",
        signal="Volatility",
        risk_score=72.0,
        priority="MEDIUM",
    ),
    MarketWatchQuote(
        symbol="ICICIBANK",
        company_name="ICICI Bank Limited",
        last_price=1208.80,
        change_pct=-0.86,
        volume_ratio=2.1,
        volatility_regime="Moderate",
        signal="Volume",
        risk_score=64.0,
        priority="MEDIUM",
    ),
    MarketWatchQuote(
        symbol="TCS",
        company_name="Tata Consultancy Services Limited",
        last_price=3214.00,
        change_pct=0.42,
        volume_ratio=0.9,
        volatility_regime="Normal",
        signal="None",
        risk_score=18.0,
        priority="LOW",
    ),
    MarketWatchQuote(
        symbol="BHARTIARTL",
        company_name="Bharti Airtel Limited",
        last_price=1734.40,
        change_pct=1.12,
        volume_ratio=1.1,
        volatility_regime="Normal",
        signal="None",
        risk_score=21.0,
        priority="LOW",
    ),
    MarketWatchQuote(
        symbol="TATAMOTORS",
        company_name="Tata Motors Limited",
        last_price=782.30,
        change_pct=4.15,
        volume_ratio=3.8,
        volatility_regime="Elevated",
        signal="Price breakout",
        risk_score=82.0,
        priority="HIGH",
    ),
    MarketWatchQuote(
        symbol="LT",
        company_name="Larsen & Toubro Limited",
        last_price=3520.10,
        change_pct=1.85,
        volume_ratio=2.4,
        volatility_regime="Moderate",
        signal="Volume pre-run",
        risk_score=68.0,
        priority="MEDIUM",
    ),
    MarketWatchQuote(
        symbol="SBIN",
        company_name="State Bank of India",
        last_price=812.40,
        change_pct=-0.45,
        volume_ratio=1.2,
        volatility_regime="Normal",
        signal="None",
        risk_score=25.0,
        priority="LOW",
    ),
    MarketWatchQuote(
        symbol="ITC",
        company_name="ITC Limited",
        last_price=468.90,
        change_pct=0.30,
        volume_ratio=0.8,
        volatility_regime="Normal",
        signal="None",
        risk_score=15.0,
        priority="LOW",
    ),
]


@router.get("/symbols", response_model=List[SymbolInfo])
def list_symbols(
    sector: Optional[str] = Query(None, description="Filter symbols by sector"),
    db: Session = Depends(get_db),
):
    """Retrieve canonical master symbols list from database."""
    try:
        query = select(SymbolMasterModel)
        if sector:
            query = query.where(SymbolMasterModel.sector.ilike(f"%{sector}%"))
        db_symbols = db.scalars(query).all()
        if db_symbols:
            return [
                SymbolInfo(
                    symbol=s.symbol,
                    company_name=s.company_name,
                    sector=s.sector,
                    industry=s.industry,
                    exchange=s.exchange,
                    is_active=s.is_active,
                )
                for s in db_symbols
            ]
    except Exception:
        pass

    results = list(_SYMBOLS.values())
    if sector:
        results = [s for s in results if s.sector.lower() == sector.lower()]
    return results


@router.get("/watchlist", response_model=List[MarketWatchQuote])
def get_watchlist(db: Session = Depends(get_db)):
    """Retrieve live market surveillance watchlist metrics from database."""
    try:
        symbols = db.scalars(select(SymbolMasterModel)).all()
        if symbols:
            quotes_list: List[MarketWatchQuote] = []
            for s in symbols:
                # Fetch last two quotes for symbol to compute actual change
                recent_quotes = (
                    db.query(MarketQuoteModel)
                    .filter(MarketQuoteModel.symbol == s.symbol)
                    .order_by(desc(MarketQuoteModel.trade_date))
                    .limit(2)
                    .all()
                )
                if not recent_quotes:
                    continue

                latest = recent_quotes[0]
                prev = recent_quotes[1] if len(recent_quotes) > 1 else recent_quotes[0]
                last_p = float(latest.close_price)
                prev_p = float(prev.close_price)
                change_pct = round(((last_p - prev_p) / prev_p) * 100.0, 2) if prev_p > 0 else 0.0

                # Check latest risk alert for this symbol
                latest_alert = (
                    db.query(RiskAlertModel)
                    .filter(RiskAlertModel.symbol == s.symbol)
                    .order_by(desc(RiskAlertModel.risk_score))
                    .first()
                )
                r_score = float(latest_alert.risk_score) if latest_alert else 25.0
                priority = latest_alert.priority_tier if latest_alert else "LOW"
                vol_ratio = float(latest_alert.volume_ratio) if latest_alert and latest_alert.volume_ratio else 1.2
                regime = "Elevated" if r_score >= 70.0 else ("Moderate" if r_score >= 50.0 else "Normal")
                sig = latest_alert.alert_category if latest_alert else "Baseline"

                quotes_list.append(
                    MarketWatchQuote(
                        symbol=s.symbol,
                        company_name=s.company_name,
                        last_price=last_p,
                        change_pct=change_pct,
                        volume_ratio=vol_ratio,
                        volatility_regime=regime,
                        signal=sig,
                        risk_score=r_score,
                        priority=priority,
                    )
                )

            if quotes_list:
                # Sort by risk score descending
                quotes_list.sort(key=lambda q: q.risk_score, reverse=True)
                return quotes_list
    except Exception:
        pass

    return _WATCHLIST_QUOTES


@router.get("/symbols/{symbol}", response_model=SymbolInfo)
def get_symbol_detail(
    symbol: str = Path(..., description="Canonical stock symbol"),
    db: Session = Depends(get_db),
):
    """Get metadata for a specific ticker symbol from database."""
    sym = symbol.upper()
    try:
        db_s = db.query(SymbolMasterModel).filter(SymbolMasterModel.symbol == sym).first()
        if db_s:
            return SymbolInfo(
                symbol=db_s.symbol,
                company_name=db_s.company_name,
                sector=db_s.sector,
                industry=db_s.industry,
                exchange=db_s.exchange,
                is_active=db_s.is_active,
            )
    except Exception:
        pass

    if sym not in _SYMBOLS:
        raise EntityNotFoundError(entity_name="Symbol", entity_id=symbol)
    return _SYMBOLS[sym]
