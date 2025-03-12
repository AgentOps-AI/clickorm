"""
Tests for ClickORM connection management.
"""

import pytest
from unittest.mock import MagicMock, patch

from clickorm import ConnectionManager
from clickorm.exceptions import ConnectionError


def test_connection_manager_init():
    """Test ConnectionManager initialization."""
    conn = ConnectionManager(
        host="localhost",
        port=9000,
        user="default",
        password="",
        database="default",
    )
    
    assert conn.host == "localhost"
    assert conn.port == 9000
    assert conn.user == "default"
    assert conn.password == ""
    assert conn.database == "default"
    assert conn._client is None


@patch("clickorm.connection.Client")
def test_connection_manager_client(mock_client):
    """Test ConnectionManager client property."""
    mock_client.return_value = MagicMock()
    
    conn = ConnectionManager()
    client = conn.client
    
    assert client is not None
    mock_client.assert_called_once_with(
        host="localhost",
        port=9000,
        user="default",
        password="",
        database="default",
    )


@patch("clickorm.connection.Client")
def test_connection_manager_execute(mock_client):
    """Test ConnectionManager execute method."""
    mock_instance = MagicMock()
    mock_instance.execute.return_value = [(1, "John")]
    mock_client.return_value = mock_instance
    
    conn = ConnectionManager()
    result = conn.execute("SELECT 1, 'John'")
    
    assert result == [(1, "John")]
    mock_instance.execute.assert_called_once_with("SELECT 1, 'John'", {})


@patch("clickorm.connection.Client")
def test_connection_manager_execute_with_params(mock_client):
    """Test ConnectionManager execute method with parameters."""
    mock_instance = MagicMock()
    mock_instance.execute.return_value = [(1, "John")]
    mock_client.return_value = mock_instance
    
    conn = ConnectionManager()
    result = conn.execute("SELECT %(id)s, %(name)s", {"id": 1, "name": "John"})
    
    assert result == [(1, "John")]
    mock_instance.execute.assert_called_once_with("SELECT %(id)s, %(name)s", {"id": 1, "name": "John"})


@patch("clickorm.connection.Client")
def test_connection_manager_execute_error(mock_client):
    """Test ConnectionManager execute method with error."""
    mock_instance = MagicMock()
    mock_instance.execute.side_effect = Exception("Connection error")
    mock_client.return_value = mock_instance
    
    conn = ConnectionManager()
    
    with pytest.raises(ConnectionError):
        conn.execute("SELECT 1")


@patch("clickorm.connection.Client")
def test_connection_manager_default(mock_client):
    """Test ConnectionManager default instance."""
    mock_client.return_value = MagicMock()
    
    conn = ConnectionManager()
    ConnectionManager.set_as_default(conn)
    
    assert ConnectionManager.get_default() is conn


@patch("clickorm.connection.Client")
def test_connection_manager_default_error(mock_client):
    """Test ConnectionManager default instance error."""
    mock_client.return_value = MagicMock()
    
    ConnectionManager._default_instance = None
    
    with pytest.raises(ConnectionError):
        ConnectionManager.get_default()
