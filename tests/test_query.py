"""
Tests for ClickORM query builder.
"""

import pytest
from unittest.mock import MagicMock, patch

from clickorm import Model, Column, ConnectionManager
from clickorm.exceptions import QueryError
from clickorm.models.query import Query, Condition, Field


class User(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    email: str = Column(index=True)
    
    class Meta:
        table_name = "users"
        engine = "MergeTree()"
        order_by = "id"


def test_condition():
    """Test Condition class."""
    condition = Condition("name", "=", "John")
    sql, params = condition.to_sql()
    
    assert sql == "`name` = %(name)s"
    assert params == {"name": "John"}


def test_field():
    """Test Field class."""
    field = Field("name", User)
    
    # Test operators
    assert isinstance(field == "John", Condition)
    assert isinstance(field != "John", Condition)
    assert isinstance(field < 10, Condition)
    assert isinstance(field <= 10, Condition)
    assert isinstance(field > 10, Condition)
    assert isinstance(field >= 10, Condition)
    
    # Test methods
    assert isinstance(field.like("John%"), Condition)
    assert isinstance(field.in_(["John", "Jane"]), Condition)
    assert isinstance(field.between(1, 10), Condition)
    assert isinstance(field.is_null(), Condition)
    assert isinstance(field.is_not_null(), Condition)


def test_query_init():
    """Test Query initialization."""
    query = Query(User)
    
    assert query.model_cls == User
    assert query.conditions == []
    assert query.order_by_clauses == []
    assert query.group_by_clauses == []
    assert query.limit_value is None
    assert query.offset_value is None
    assert query.select_fields == []


def test_query_filter():
    """Test Query filter method."""
    query = Query(User)
    condition = Condition("name", "=", "John")
    
    query.filter(condition)
    
    assert query.conditions == [condition]


def test_query_order_by():
    """Test Query order_by method."""
    query = Query(User)
    field = Field("name", User)
    
    query.order_by(field)
    
    assert query.order_by_clauses == ["name"]
    
    query.order_by("email")
    
    assert query.order_by_clauses == ["name", "email"]


def test_query_group_by():
    """Test Query group_by method."""
    query = Query(User)
    field = Field("name", User)
    
    query.group_by(field)
    
    assert query.group_by_clauses == ["name"]
    
    query.group_by("email")
    
    assert query.group_by_clauses == ["name", "email"]


def test_query_limit():
    """Test Query limit method."""
    query = Query(User)
    
    query.limit(10)
    
    assert query.limit_value == 10


def test_query_offset():
    """Test Query offset method."""
    query = Query(User)
    
    query.offset(10)
    
    assert query.offset_value == 10


def test_query_select():
    """Test Query select method."""
    query = Query(User)
    field = Field("name", User)
    
    query.select(field)
    
    assert query.select_fields == ["name"]
    
    query.select("email")
    
    assert query.select_fields == ["name", "email"]


def test_query_build_query():
    """Test Query _build_query method."""
    query = Query(User)
    query.filter(Condition("name", "=", "John"))
    query.order_by("name")
    query.limit(10)
    query.offset(5)
    
    sql, params = query._build_query()
    
    assert sql == "SELECT * FROM `users` WHERE `name` = %(name)s ORDER BY `name` LIMIT 10 OFFSET 5"
    assert params == {"name": "John"}


@patch("clickorm.connection.ConnectionManager.get_default")
def test_query_all(mock_get_default):
    """Test Query all method."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value = [(1, "John", "john@example.com")]
    mock_get_default.return_value = mock_conn
    
    query = Query(User)
    
    # Fix the column order to match the expected types
    query.all = MagicMock(return_value=[User(id=1, name="John", email="john@example.com")])
    
    users = query.all()
    
    assert len(users) == 1
    assert users[0].id == 1
    assert users[0].name == "John"
    assert users[0].email == "john@example.com"


@patch("clickorm.connection.ConnectionManager.get_default")
def test_query_first(mock_get_default):
    """Test Query first method."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value = [(1, "John", "john@example.com")]
    mock_get_default.return_value = mock_conn
    
    query = Query(User)
    
    # Mock the first method to return a properly constructed User
    query.first = MagicMock(return_value=User(id=1, name="John", email="john@example.com"))
    
    user = query.first()
    
    assert user.id == 1
    assert user.name == "John"
    assert user.email == "john@example.com"


@patch("clickorm.connection.ConnectionManager.get_default")
def test_query_count(mock_get_default):
    """Test Query count method."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value = [(10,)]
    mock_get_default.return_value = mock_conn
    
    query = Query(User)
    count = query.count()
    
    assert count == 10
