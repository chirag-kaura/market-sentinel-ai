"""
PostgreSQL Database Session Lifecycle and Connection Pooling.
Phase 10 — Step 10.2: Configures SQLAlchemy engine, connection pooling parameters,
and FastAPI dependency injection for database session management.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.models.market import Base

# Database URL from environment with local fallback for testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./market_sentinel.db")

# Connection pool configuration optimized for low memory usage
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,          # Bounded pool size per hardware guidelines
        max_overflow=10,
        pool_pre_ping=True,   # Validates connections before checkout
        pool_recycle=1800     # Recycles idle connections every 30 mins
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a scoped database session and ensuring proper cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None) -> None:
    """Initializes tables for all registered SQLAlchemy models."""
    active_engine = target_engine or engine
    Base.metadata.create_all(bind=active_engine)
