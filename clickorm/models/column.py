"""
Column definitions for ClickORM models.
"""

from typing import Any, Callable, Dict, Optional, Type, Union

from pydantic import Field

from clickorm import types


class Column:
    """
    Represents a column in a ClickHouse table.
    
    This class is used to define columns in ClickORM models.
    """

    def __init__(
        self,
        clickhouse_type: Optional[str] = None,
        primary_key: bool = False,
        nullable: bool = False,
        default: Any = None,
        index: bool = False,
        unique: bool = False,
        comment: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize a new Column.
        
        Args:
            clickhouse_type: The ClickHouse type for the column.
            primary_key: Whether the column is a primary key.
            nullable: Whether the column is nullable.
            default: The default value for the column.
            index: Whether the column should be indexed.
            unique: Whether the column should have a unique constraint.
            comment: A comment for the column.
            **kwargs: Additional arguments to pass to Pydantic's Field.
        """
        self.clickhouse_type = clickhouse_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.index = index
        self.unique = unique
        self.comment = comment
        self.kwargs = kwargs
        
        # These will be set when the column is bound to a model
        self.name = None
        self.python_type = None
        self.model_cls = None

    def __set_name__(self, owner: Type, name: str) -> None:
        """
        Set the name of the column.
        
        This method is called when the column is bound to a model.
        
        Args:
            owner: The model class.
            name: The name of the column.
        """
        self.name = name
        self.model_cls = owner

    def get_field(self) -> Field:
        """
        Get the Pydantic Field for this column.
        
        Returns:
            The Pydantic Field.
        """
        field_kwargs = self.kwargs.copy()
        
        if self.default is not None:
            if callable(self.default):
                field_kwargs["default_factory"] = self.default
            else:
                field_kwargs["default"] = self.default
        
        return Field(**field_kwargs)

    def get_clickhouse_type(self, python_type: Type) -> str:
        """
        Get the ClickHouse type for this column.
        
        Args:
            python_type: The Python type of the column.
            
        Returns:
            The ClickHouse type as a string.
        """
        self.python_type = python_type
        
        if self.clickhouse_type is not None:
            return self.clickhouse_type
        
        return types.get_clickhouse_type(python_type)

    def get_column_definition(self) -> str:
        """
        Get the ClickHouse column definition.
        
        Returns:
            The ClickHouse column definition as a string.
        """
        if self.name is None or self.python_type is None:
            raise ValueError("Column is not bound to a model")
        
        clickhouse_type = self.get_clickhouse_type(self.python_type)
        
        if self.nullable:
            clickhouse_type = f"Nullable({clickhouse_type})"
        
        definition = f"`{self.name}` {clickhouse_type}"
        
        if self.comment:
            definition += f" COMMENT '{self.comment}'"
        
        return definition
