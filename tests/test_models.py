"""
Tests for ClickORM models.
"""

import pytest
from datetime import datetime
from typing import List, Optional

from clickorm import Model, Column, ConnectionManager, types
from clickorm.exceptions import ValidationError


class User(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    email: str = Column(index=True)
    created_at: datetime = Column(default=datetime.utcnow)
    
    class Meta:
        table_name = "users"
        engine = "MergeTree()"
        order_by = "id"


def test_model_definition():
    """Test model definition."""
    # Check that the model has the correct columns
    columns = User.get_columns()
    assert "id" in columns
    assert "name" in columns
    assert "email" in columns
    assert "created_at" in columns
    
    # Check that the columns have the correct attributes
    assert columns["id"].primary_key
    assert columns["email"].index
    assert callable(columns["created_at"].default)
    
    # Check that the model has the correct table name
    assert User.get_table_name() == "users"


def test_model_validation():
    """Test model validation."""
    # Valid model
    user = User(id=1, name="John Doe", email="john@example.com")
    assert user.id == 1
    assert user.name == "John Doe"
    assert user.email == "john@example.com"
    
    # Invalid model (missing required fields)
    with pytest.raises(ValidationError):
        User(id=1)


def test_model_to_dict():
    """Test model to_dict method."""
    user = User(id=1, name="John Doe", email="john@example.com")
    data = user.to_dict()
    
    assert data["id"] == 1
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert "created_at" in data


def test_model_from_dict():
    """Test model from_dict method."""
    data = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
    }
    
    user = User.from_dict(data)
    
    assert user.id == 1
    assert user.name == "John Doe"
    assert user.email == "john@example.com"


def test_model_from_row():
    """Test model from_row method."""
    row = (1, "John Doe", "john@example.com", datetime(2023, 1, 1))
    columns = ["id", "name", "email", "created_at"]
    
    user = User.from_row(row, columns)
    
    assert user.id == 1
    assert user.name == "John Doe"
    assert user.email == "john@example.com"
    assert user.created_at == datetime(2023, 1, 1)
