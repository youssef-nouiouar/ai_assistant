# ============================================================================
# FICHIER : backend/test/conftest.py
# ============================================================================
import sys
sys.path.append('.')
import pytest
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings
from app.models.base import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create test database and engine"""
    test_db_name = "ai_it_assistant"
    
    # Build URLs
    test_db_url = settings.DATABASE_URL.replace("ai_it_assistant", test_db_name)
    admin_url = settings.DATABASE_URL.rsplit('/', 1)[0] + '/postgres'
    
    # Create database if it doesn't exist
    admin_engine = create_engine(admin_url)
    with admin_engine.connect() as conn:
        conn.connection.autocommit = True
        try:
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
            print(f"✓ Created test database: {test_db_name}")
        except Exception as e:
            print(f"Database creation warning: {e}")
    
    admin_engine.dispose()
    
    # Create engine for test database
    engine = create_engine(test_db_url, echo=False)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Created all tables")
    
    yield engine
    
    # Cleanup
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provide a fresh database session for each test"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()