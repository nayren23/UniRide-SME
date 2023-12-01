"""conftest.py"""
from unittest.mock import MagicMock
import pytest
from uniride_sme import connect_pg, app
from uniride_sme.config import TestingConfig


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    # Setup testing config
    app.config.from_object(TestingConfig)


@pytest.fixture(scope="function", autouse=True)
def mock_connect(monkeypatch):
    """Mock the method connect from connect_pg"""
    mock_conn = MagicMock()
    monkeypatch.setattr(connect_pg, "connect", MagicMock(return_value=mock_conn))
    mock_conn.return_value = None
    return mock_conn


@pytest.fixture
def mock_disconnect(monkeypatch):
    """Mock the method disconnect from connect_pg"""
    mock_close = MagicMock()
    monkeypatch.setattr(connect_pg, "disconnect", mock_close)
    return mock_close


@pytest.fixture
def mock_execute_command(monkeypatch):
    """Mock the method execute_command from connect_pg"""
    mock_execute = MagicMock()
    monkeypatch.setattr(connect_pg, "execute_command", mock_execute)
    return mock_execute


@pytest.fixture
def mock_get_query(monkeypatch):
    """Mock the method get_query from connect_pg"""
    mock_query = MagicMock()
    monkeypatch.setattr(connect_pg, "get_query", mock_query)
    return mock_query
