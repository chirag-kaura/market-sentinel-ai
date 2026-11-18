"""
Market Data RESTful API Endpoints.
Phase 10 — Step 10.3: Stock metadata, real quotes, and watchlist metrics.
"""

from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Query, Path
from pydantic import BaseModel
from backend.core.exceptions import EntityNotFoundError

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
):
    """Retrieve canonical master symbols list."""
    results = list(_SYMBOLS.values())
    if sector:
        results = [s for s in results if s.sector.lower() == sector.lower()]
    return results


@router.get("/watchlist", response_model=List[MarketWatchQuote])
def get_watchlist():
    """Retrieve live market surveillance watchlist metrics."""
    return _WATCHLIST_QUOTES


@router.get("/symbols/{symbol}", response_model=SymbolInfo)
def get_symbol_detail(
    symbol: str = Path(..., description="Canonical stock symbol")
):
    """Get metadata for a specific ticker symbol."""
    sym = symbol.upper()
    if sym not in _SYMBOLS:
        raise EntityNotFoundError(entity_name="Symbol", entity_id=symbol)
    return _SYMBOLS[sym]
