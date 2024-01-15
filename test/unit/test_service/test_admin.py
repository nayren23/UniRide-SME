import datetime
from unittest.mock import MagicMock, patch
import pytest
from uniride_sme.service.user_service import (
    users_information,
    verify_user,
    delete_user,
    user_information_id,
    user_stat_passenger,
    user_stat_driver,
)
from uniride_sme.utils.exception.user_exceptions import UserNotFoundException

# Mocking the database connection and query functions
@pytest.fixture
def mock_connect_pg(monkeypatch):
    mock_conn = MagicMock()
    mock_get_query = MagicMock()
    mock_execute_command = MagicMock()
    monkeypatch.setattr("uniride_sme.service.user_service.connect_pg.connect", mock_conn)
    monkeypatch.setattr("uniride_sme.service.user_service.connect_pg.get_query", mock_get_query)
    monkeypatch.setattr("uniride_sme.service.user_service.connect_pg.execute_command", mock_execute_command)
    return mock_conn, mock_get_query, mock_execute_command


def test_users_information(mock_connect_pg):
    """Test users_information function"""
    mock_conn, mock_get_query, _ = mock_connect_pg
    mock_get_query.return_value = [
        (1, 2, "Last", "First", "profile.jpg", datetime.datetime(2022, 1, 1), datetime.datetime(2022, 1, 2)),
    ]
    result = users_information()
    assert len(result) == 1
    assert result[0]["id_user"] == 1
    assert result[0]["lastname"] == "Last"
    assert result[0]["firstname"] == "First"


def test_verify_user_existing(mock_connect_pg):
    """Test verify_user function for an existing user"""
    mock_conn, mock_get_query, _ = mock_connect_pg
    mock_get_query.return_value = [(1,)]
    verify_user(1)
    mock_conn.assert_called_once()
    mock_conn.return_value.close.assert_called_once()


def test_verify_user_non_existing(mock_connect_pg):
    """Test verify_user function for a non-existing user"""
    mock_conn, mock_get_query, _ = mock_connect_pg
    mock_get_query.return_value = []
    with pytest.raises(UserNotFoundException):
        verify_user(1)
    mock_conn.assert_called_once()
    mock_conn.return_value.close.assert_called_once()

def test_delete_user_existing(mock_connect_pg):
    """Test delete_user function for an existing user"""
    mock_conn, _, mock_execute_command = mock_connect_pg
    # Mocking the result of the verify_user function
    with patch("uniride_sme.service.user_service.verify_user") as verify_user_mock:
        verify_user_mock.return_value = None
        delete_user(1)

    # Verify that the connection was opened and closed
    mock_conn.assert_called_once()
    # Verify that verify_user was called with the correct parameter
    verify_user_mock.assert_called_once_with(1)
    # Verify that execute_command was called with the correct query and values
    mock_execute_command.assert_called_once_with(mock_conn.return_value, "DELETE FROM uniride.ur_user WHERE u_id = %s", (1,))
    # Verify that the connection was closed
    mock_conn.return_value.close.assert_called_once()
