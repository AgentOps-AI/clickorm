"""
Exceptions for ClickORM.
"""


class ClickORMError(Exception):
    """Base exception for all ClickORM errors."""

    pass


class ConnectionError(ClickORMError):
    """Raised when there is an error with the database connection."""

    pass


class QueryError(ClickORMError):
    """Raised when there is an error with a query."""

    pass


class ValidationError(ClickORMError):
    """Raised when there is a validation error with a model."""

    pass


class SchemaError(ClickORMError):
    """Raised when there is an error with a schema operation."""

    pass
