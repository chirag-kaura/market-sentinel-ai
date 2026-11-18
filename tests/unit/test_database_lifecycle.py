"""Unit tests for Database Session Management (Phase 10 — Step 10.2)."""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from backend.core.database import get_db, init_db
from backend.models.market import Base, SymbolMasterModel


@pytest.fixture
def test_engine():
    engine = create_engine("sqlite:///:memory:")
    return engine


def test_database_initialization(test_engine):
    init_db(target_engine=test_engine)
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    assert "symbol_master" in tables


def test_get_db_session_lifecycle(monkeypatch):
    test_db_file = "test_lifecycle.db"
    test_engine = create_engine(f"sqlite:///{test_db_file}", connect_args={"check_same_thread": False})
    init_db(target_engine=test_engine)
    
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr("backend.core.database.SessionLocal", TestSession)

    db_gen = get_db()
    session = next(db_gen)
    assert session is not None
    try:
        res = session.query(SymbolMasterModel).all()
        assert res == []
    finally:
        with pytest.raises(StopIteration):
            next(db_gen)
    
    # Clean up file
    import os
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except OSError:
            pass

