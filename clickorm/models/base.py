"""
Base model for ClickORM.
"""

import inspect
from typing import Any, ClassVar, Dict, List, Optional, Set, Type, TypeVar, get_type_hints

from pydantic import BaseModel, create_model

from clickorm.connection import ConnectionManager
from clickorm.exceptions import QueryError, SchemaError, ValidationError
from clickorm.models.column import Column
from clickorm.models.query import Query


T = TypeVar("T", bound="Model")


class ModelMeta(type):
    """
    Metaclass for Model.
    
    This metaclass processes column definitions and sets up the Pydantic model.
    """

    def __new__(mcs, name, bases, namespace):
        # Skip processing for the base Model class
        if name == "Model" and namespace.get("__module__") == __name__:
            return super().__new__(mcs, name, bases, namespace)
        
        # Get columns from the namespace
        columns = {}
        annotations = {}
        
        for key, value in list(namespace.items()):
            if isinstance(value, Column):
                columns[key] = value
        
        # Get type hints
        if "__annotations__" in namespace:
            annotations = namespace["__annotations__"]
        
        # Create Pydantic fields
        fields = {}
        for field_name, column in columns.items():
            if field_name in annotations:
                python_type = annotations[field_name]
                fields[field_name] = (python_type, column.get_field())
        
        # Create the class
        cls = super().__new__(mcs, name, bases, namespace)
        
        # Create the Pydantic model
        pydantic_model = create_model(
            f"{name}Model",
            __base__=BaseModel,
            **fields,
        )
        
        # Set the Pydantic model on the class
        cls.__pydantic_model__ = pydantic_model
        
        # Set column attributes
        for field_name, column in columns.items():
            if field_name in annotations:
                column.__set_name__(cls, field_name)
                column.python_type = annotations[field_name]
        
        return cls


class Model(metaclass=ModelMeta):
    """
    Base model for ClickORM.
    
    This class provides the base functionality for all ClickORM models.
    """

    # Class variables
    __columns__: ClassVar[Dict[str, Column]] = {}
    __pydantic_model__: ClassVar[Type[BaseModel]] = None
    
    class Meta:
        """
        Metadata for the model.
        
        This class is used to define metadata for the model, such as the table name,
        engine, and order by clause.
        """
        
        table_name: Optional[str] = None
        engine: str = "MergeTree()"
        order_by: Optional[str] = None
        partition_by: Optional[str] = None
        primary_key: Optional[str] = None
        sample_by: Optional[str] = None
        ttl: Optional[str] = None
        settings: Optional[Dict[str, Any]] = None
    
    def __init__(self, **data: Any):
        """
        Initialize a new model instance.
        
        Args:
            **data: The data to initialize the model with.
        """
        # Create a Pydantic model instance
        try:
            self.__pydantic_instance__ = self.__class__.__pydantic_model__(**data)
        except Exception as e:
            raise ValidationError(f"Failed to validate model: {e}")
        
        # Set attributes from the Pydantic model
        for key, value in self.__pydantic_instance__.model_dump().items():
            setattr(self, key, value)
    
    @classmethod
    def get_table_name(cls) -> str:
        """
        Get the table name for the model.
        
        Returns:
            The table name.
        """
        if hasattr(cls.Meta, "table_name") and cls.Meta.table_name:
            return cls.Meta.table_name
        return cls.__name__.lower()
    
    @classmethod
    def get_columns(cls) -> Dict[str, Column]:
        """
        Get the columns for the model.
        
        Returns:
            A dictionary of column names to Column instances.
        """
        if not hasattr(cls, "__columns_cache__"):
            columns = {}
            for name, attr in inspect.getmembers(cls):
                if isinstance(attr, Column):
                    columns[name] = attr
            cls.__columns_cache__ = columns
        return cls.__columns_cache__
    
    @classmethod
    def get_primary_key_columns(cls) -> List[Column]:
        """
        Get the primary key columns for the model.
        
        Returns:
            A list of primary key Column instances.
        """
        return [col for col in cls.get_columns().values() if col.primary_key]
    
    @classmethod
    def create_table(cls, if_not_exists: bool = True) -> None:
        """
        Create the table for the model.
        
        Args:
            if_not_exists: Whether to add IF NOT EXISTS to the query.
        """
        conn = ConnectionManager.get_default()
        
        # Get columns
        columns = cls.get_columns()
        if not columns:
            raise SchemaError("No columns defined for model")
        
        # Build column definitions
        column_defs = []
        for name, column in columns.items():
            column_defs.append(column.get_column_definition())
        
        # Build table options
        table_options = []
        
        if hasattr(cls.Meta, "engine") and cls.Meta.engine:
            table_options.append(f"ENGINE = {cls.Meta.engine}")
        
        if hasattr(cls.Meta, "order_by") and cls.Meta.order_by:
            table_options.append(f"ORDER BY ({cls.Meta.order_by})")
        
        if hasattr(cls.Meta, "partition_by") and cls.Meta.partition_by:
            table_options.append(f"PARTITION BY {cls.Meta.partition_by}")
        
        if hasattr(cls.Meta, "primary_key") and cls.Meta.primary_key:
            table_options.append(f"PRIMARY KEY ({cls.Meta.primary_key})")
        
        if hasattr(cls.Meta, "sample_by") and cls.Meta.sample_by:
            table_options.append(f"SAMPLE BY {cls.Meta.sample_by}")
        
        if hasattr(cls.Meta, "ttl") and cls.Meta.ttl:
            table_options.append(f"TTL {cls.Meta.ttl}")
        
        if hasattr(cls.Meta, "settings") and cls.Meta.settings:
            settings = ", ".join(f"{k}={v}" for k, v in cls.Meta.settings.items())
            table_options.append(f"SETTINGS {settings}")
        
        # Build the query
        query = f"CREATE TABLE {'IF NOT EXISTS ' if if_not_exists else ''}`{cls.get_table_name()}` (\n"
        query += ",\n".join(f"    {col_def}" for col_def in column_defs)
        query += "\n)"
        
        if table_options:
            query += "\n" + "\n".join(table_options)
        
        # Execute the query
        try:
            conn.execute(query)
        except Exception as e:
            raise SchemaError(f"Failed to create table: {e}")
    
    @classmethod
    def drop_table(cls, if_exists: bool = True) -> None:
        """
        Drop the table for the model.
        
        Args:
            if_exists: Whether to add IF EXISTS to the query.
        """
        conn = ConnectionManager.get_default()
        
        query = f"DROP TABLE {'IF EXISTS ' if if_exists else ''}`{cls.get_table_name()}`"
        
        try:
            conn.execute(query)
        except Exception as e:
            raise SchemaError(f"Failed to drop table: {e}")
    
    @classmethod
    def alter_table(
        cls,
        add_column: Optional[Column] = None,
        drop_column: Optional[str] = None,
        modify_column: Optional[Column] = None,
    ) -> None:
        """
        Alter the table for the model.
        
        Args:
            add_column: A Column to add.
            drop_column: The name of a column to drop.
            modify_column: A Column to modify.
        """
        conn = ConnectionManager.get_default()
        
        if add_column:
            query = f"ALTER TABLE `{cls.get_table_name()}` ADD COLUMN {add_column.get_column_definition()}"
        elif drop_column:
            query = f"ALTER TABLE `{cls.get_table_name()}` DROP COLUMN `{drop_column}`"
        elif modify_column:
            query = f"ALTER TABLE `{cls.get_table_name()}` MODIFY COLUMN {modify_column.get_column_definition()}"
        else:
            raise SchemaError("No alter operation specified")
        
        try:
            conn.execute(query)
        except Exception as e:
            raise SchemaError(f"Failed to alter table: {e}")
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a model instance from a dictionary.
        
        Args:
            data: The data to initialize the model with.
            
        Returns:
            A new model instance.
        """
        return cls(**data)
    
    @classmethod
    def from_row(cls: Type[T], row: tuple, columns: List[str]) -> T:
        """
        Create a model instance from a database row.
        
        Args:
            row: The database row.
            columns: The column names.
            
        Returns:
            A new model instance.
        """
        # Create a dictionary with the correct types for each column
        data = {}
        for i, col_name in enumerate(columns):
            if i < len(row):
                # Get the column definition
                columns_dict = cls.get_columns()
                if col_name in columns_dict:
                    # Convert the value to the correct type
                    col = columns_dict[col_name]
                    if col.python_type == int and isinstance(row[i], str):
                        try:
                            data[col_name] = int(row[i])
                        except (ValueError, TypeError):
                            data[col_name] = 0
                    elif col.python_type == str and not isinstance(row[i], str):
                        data[col_name] = str(row[i])
                    else:
                        data[col_name] = row[i]
                else:
                    data[col_name] = row[i]
        
        try:
            return cls.from_dict(data)
        except ValidationError:
            # If validation fails, try to create a model with default values
            default_data = {col_name: None for col_name in columns}
            for col_name, col in cls.get_columns().items():
                if col.default is not None:
                    default_value = col.default() if callable(col.default) else col.default
                    default_data[col_name] = default_value
            
            # Update with any valid data
            for col_name, value in data.items():
                if col_name in cls.get_columns():
                    default_data[col_name] = value
            
            return cls.from_dict(default_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model instance to a dictionary.
        
        Returns:
            A dictionary representation of the model.
        """
        return self.__pydantic_instance__.model_dump()
    
    def save(self) -> None:
        """
        Save the model instance to the database.
        
        If the model has a primary key and it exists in the database, the model
        will be updated. Otherwise, it will be inserted.
        """
        conn = ConnectionManager.get_default()
        
        # Get data
        data = self.to_dict()
        
        # Get primary key columns
        pk_columns = self.__class__.get_primary_key_columns()
        
        # Check if the model exists
        if pk_columns:
            where_clauses = []
            params = {}
            
            for col in pk_columns:
                if col.name in data:
                    where_clauses.append(f"`{col.name}` = %({col.name})s")
                    params[col.name] = data[col.name]
            
            if where_clauses:
                query = f"SELECT 1 FROM `{self.__class__.get_table_name()}` WHERE {' AND '.join(where_clauses)} LIMIT 1"
                result = conn.execute(query, params)
                
                if result:
                    # Update
                    set_clauses = []
                    update_params = {}
                    
                    for name, value in data.items():
                        if name not in [col.name for col in pk_columns]:
                            set_clauses.append(f"`{name}` = %({name})s")
                            update_params[name] = value
                    
                    if set_clauses:
                        update_params.update(params)
                        query = f"ALTER TABLE `{self.__class__.get_table_name()}` UPDATE {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
                        conn.execute(query, update_params)
                    
                    return
        
        # Insert
        columns = [f"`{name}`" for name in data.keys()]
        placeholders = [f"%({name})s" for name in data.keys()]
        
        query = f"INSERT INTO `{self.__class__.get_table_name()}` ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        try:
            conn.execute(query, data)
        except Exception as e:
            raise QueryError(f"Failed to insert model: {e}")
    
    def delete(self) -> None:
        """
        Delete the model instance from the database.
        """
        conn = ConnectionManager.get_default()
        
        # Get data
        data = self.to_dict()
        
        # Get primary key columns
        pk_columns = self.__class__.get_primary_key_columns()
        
        if not pk_columns:
            raise QueryError("Cannot delete model without primary key")
        
        where_clauses = []
        params = {}
        
        for col in pk_columns:
            if col.name in data:
                where_clauses.append(f"`{col.name}` = %({col.name})s")
                params[col.name] = data[col.name]
        
        if not where_clauses:
            raise QueryError("Cannot delete model without primary key values")
        
        query = f"ALTER TABLE `{self.__class__.get_table_name()}` DELETE WHERE {' AND '.join(where_clauses)}"
        
        try:
            conn.execute(query, params)
        except Exception as e:
            raise QueryError(f"Failed to delete model: {e}")
    
    @classmethod
    @property
    def query(cls) -> Query:
        """
        Get a query builder for the model.
        
        Returns:
            A Query instance.
        """
        return Query(cls)
