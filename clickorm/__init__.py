"""
ClickORM: Python ORM framework for ClickHouse with Pydantic integration.
"""

from clickorm.connection import ConnectionManager
from clickorm.exceptions import (
    ClickORMError,
    ConnectionError,
    QueryError,
    ValidationError,
    SchemaError,
)
from clickorm.models import Model, Column, Field
from clickorm import types

__version__ = "0.1.0"
__all__ = [
    "ConnectionManager",
    "Model",
    "Column",
    "Field",
    "types",
    "ClickORMError",
    "ConnectionError",
    "QueryError",
    "ValidationError",
    "SchemaError",
]
