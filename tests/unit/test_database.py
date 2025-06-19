import pytest
from unittest import mock

# Happy path: get_db yields a session and closes it
def test_get_db_happy_path(mock_sqlite_env, mock_sessionlocal):
    from src.database import database
    with mock.patch.object(database, 'get_sessionlocal', return_value=mock_sessionlocal):
        mock_session = mock_sessionlocal.return_value
        gen = database.get_db()
        db = next(gen)
        assert db is mock_session
        # Simulate closing
        with mock.patch.object(mock_session, 'close') as mock_close, \
             mock.patch.object(mock_sessionlocal, 'remove') as mock_remove:
            try:
                next(gen)
            except StopIteration:
                pass
            mock_close.assert_called_once()
            mock_remove.assert_called_once()

# Edge case: missing SQLITE_DATABASE_PATH env var
def test_get_db_missing_env(monkeypatch):
    monkeypatch.delenv("SQLITE_DATABASE_PATH", raising=False)
    from src.database import database
    with pytest.raises(ValueError, match="SQLITE_DATABASE_PATH environment variable is not set"):
        database.get_engine()

# Edge case: DB connection failure
def test_get_db_db_connection_failure(monkeypatch):
    with mock.patch("src.database.database.create_engine", side_effect=Exception("DB fail")):
        from src.database import database
        with pytest.raises(Exception, match="DB fail"):
            database.get_engine()