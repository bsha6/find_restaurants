from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
import os
from contextlib import contextmanager

Base = declarative_base()

def get_engine():
    db_path = os.getenv('SQLITE_DATABASE_PATH')
    if not db_path:
        raise ValueError("SQLITE_DATABASE_PATH environment variable is not set")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    return create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

def get_sessionlocal():
    engine = get_engine()
    SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(SessionFactory)

_sessionlocal = None

def _get_sessionlocal_instance():
    global _sessionlocal
    if _sessionlocal is None:
        _sessionlocal = get_sessionlocal()
    return _sessionlocal

@contextmanager
def get_db():
    session_local = _get_sessionlocal_instance()
    db = session_local()
    try:
        yield db
    finally:
        session_local.remove() 