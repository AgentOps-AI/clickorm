"""
Query builder for ClickORM.
"""

from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

from clickorm.connection import ConnectionManager
from clickorm.exceptions import QueryError, ValidationError

T = TypeVar("T")


class Condition:
    """
    Represents a query condition.
    """

    def __init__(self, field: str, operator: str, value: Any):
        """
        Initialize a new Condition.
        
        Args:
            field: The field name.
            operator: The operator.
            value: The value.
        """
        self.field = field
        self.operator = operator
        self.value = value
    
    def to_sql(self) -> Tuple[str, Dict[str, Any]]:
        """
        Convert the condition to SQL.
        
        Returns:
            A tuple of (sql, params).
        """
        param_name = f"{self.field.replace('.', '_')}"
        return f"`{self.field}` {self.operator} %({param_name})s", {param_name: self.value}


class Field:
    """
    Represents a field in a query.
    """

    def __init__(self, name: str, model_cls: Type):
        """
        Initialize a new Field.
        
        Args:
            name: The field name.
            model_cls: The model class.
        """
        self.name = name
        self.model_cls = model_cls
    
    def __eq__(self, other: Any) -> Condition:
        """
        Create an equality condition.
        
        Args:
            other: The value to compare with.
            
        Returns:
            A Condition.
        """
        return Condition(self.name, "=", other)
    
    def __ne__(self, other: Any) -> Condition:
        """
        Create an inequality condition.
        
        Args:
            other: The value to compare with.
            
        Returns:
            A Condition.
        """
        return Condition(self.name, "!=", other)
    
    def __lt__(self, other: Any) -> Condition:
        """
        Create a less than condition.
        
        Args:
            other: The value to compare with.
            
        Returns:
            A Condition.
        """
        return Condition(self.name, "<", other)
    
    def __le__(self, other: Any) -> Condition:
        """
        Create a less than or equal condition.
        
        Args:
            other: The value to compare with.
            
        Returns:
            A Condition.
        """
        return Condition(self.name, "<=", other)
    
    def __gt__(self, other: Any) -> Condition:
        """
        Create a greater than condition.
        
        Args:
            other: The value to compare with.
            
        Returns:
            A Condition.
        """
        return Condition(self.name, ">", other)
    
    def __ge__(self, other: Any) -> Condition:
        """
        Create a greater than or equal condition.
        
        Args:
            other: The value to compare with.
            
        Returns:
            A Condition.
        """
        return Condition(self.name, ">=", other)
    
    def like(self, pattern: str) -> Condition:
        """
        Create a LIKE condition.
        
        Args:
            pattern: The pattern to match.
            
        Returns:
            A Condition.
        """
        return Condition(self.name, "LIKE", pattern)
    
    def in_(self, values: List[Any]) -> Condition:
        """
        Create an IN condition.
        
        Args:
            values: The values to match.
            
        Returns:
            A Condition.
        """
        return Condition(self.name, "IN", values)
    
    def between(self, start: Any, end: Any) -> Condition:
        """
        Create a BETWEEN condition.
        
        Args:
            start: The start value.
            end: The end value.
            
        Returns:
            A Condition.
        """
        return Condition(self.name, "BETWEEN", (start, end))
    
    def is_null(self) -> Condition:
        """
        Create an IS NULL condition.
        
        Returns:
            A Condition.
        """
        return Condition(self.name, "IS NULL", None)
    
    def is_not_null(self) -> Condition:
        """
        Create an IS NOT NULL condition.
        
        Returns:
            A Condition.
        """
        return Condition(self.name, "IS NOT NULL", None)


class Query(Generic[T]):
    """
    Query builder for ClickORM.
    """

    def __init__(self, model_cls: Type[T]):
        """
        Initialize a new Query.
        
        Args:
            model_cls: The model class.
        """
        self.model_cls = model_cls
        self.conditions = []
        self.order_by_clauses = []
        self.group_by_clauses = []
        self.limit_value = None
        self.offset_value = None
        self.select_fields = []
    
    def __getattr__(self, name: str) -> Field:
        """
        Get a field.
        
        Args:
            name: The field name.
            
        Returns:
            A Field.
        """
        return Field(name, self.model_cls)
    
    def filter(self, *conditions: Condition) -> "Query[T]":
        """
        Add filter conditions.
        
        Args:
            *conditions: The conditions to add.
            
        Returns:
            The Query instance.
        """
        self.conditions.extend(conditions)
        return self
    
    def order_by(self, *fields: Union[Field, str]) -> "Query[T]":
        """
        Add order by clauses.
        
        Args:
            *fields: The fields to order by.
            
        Returns:
            The Query instance.
        """
        for field in fields:
            if isinstance(field, Field):
                self.order_by_clauses.append(field.name)
            elif isinstance(field, str):
                self.order_by_clauses.append(field)
        return self
    
    def group_by(self, *fields: Union[Field, str]) -> "Query[T]":
        """
        Add group by clauses.
        
        Args:
            *fields: The fields to group by.
            
        Returns:
            The Query instance.
        """
        for field in fields:
            if isinstance(field, Field):
                self.group_by_clauses.append(field.name)
            elif isinstance(field, str):
                self.group_by_clauses.append(field)
        return self
    
    def limit(self, value: int) -> "Query[T]":
        """
        Set the limit.
        
        Args:
            value: The limit value.
            
        Returns:
            The Query instance.
        """
        self.limit_value = value
        return self
    
    def offset(self, value: int) -> "Query[T]":
        """
        Set the offset.
        
        Args:
            value: The offset value.
            
        Returns:
            The Query instance.
        """
        self.offset_value = value
        return self
    
    def select(self, *fields: Union[Field, str]) -> "Query[T]":
        """
        Set the select fields.
        
        Args:
            *fields: The fields to select.
            
        Returns:
            The Query instance.
        """
        for field in fields:
            if isinstance(field, Field):
                self.select_fields.append(field.name)
            elif isinstance(field, str):
                self.select_fields.append(field)
        return self
    
    def _build_query(self) -> Tuple[str, Dict[str, Any]]:
        """
        Build the query.
        
        Returns:
            A tuple of (query, params).
        """
        # Build the SELECT clause
        if self.select_fields:
            select_clause = ", ".join(f"`{field}`" for field in self.select_fields)
        else:
            select_clause = "*"
        
        # Build the FROM clause
        from_clause = f"`{self.model_cls.get_table_name()}`"
        
        # Build the WHERE clause
        where_clauses = []
        params = {}
        
        for condition in self.conditions:
            sql, condition_params = condition.to_sql()
            where_clauses.append(sql)
            params.update(condition_params)
        
        # Build the ORDER BY clause
        order_by_clause = ", ".join(f"`{field}`" for field in self.order_by_clauses)
        
        # Build the GROUP BY clause
        group_by_clause = ", ".join(f"`{field}`" for field in self.group_by_clauses)
        
        # Build the query
        query = f"SELECT {select_clause} FROM {from_clause}"
        
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        if group_by_clause:
            query += f" GROUP BY {group_by_clause}"
        
        if order_by_clause:
            query += f" ORDER BY {order_by_clause}"
        
        if self.limit_value is not None:
            query += f" LIMIT {self.limit_value}"
        
        if self.offset_value is not None:
            query += f" OFFSET {self.offset_value}"
        
        return query, params
    
    def all(self) -> List[T]:
        """
        Execute the query and return all results.
        
        Returns:
            A list of model instances.
        """
        conn = ConnectionManager.get_default()
        
        query, params = self._build_query()
        
        try:
            result = conn.execute(query, params)
        except Exception as e:
            raise QueryError(f"Failed to execute query: {e}")
        
        # Get column names
        if self.select_fields:
            columns = self.select_fields
        else:
            columns = list(self.model_cls.get_columns().keys())
        
        # Create model instances
        return [self.model_cls.from_row(row, columns) for row in result]
    
    def first(self) -> Optional[T]:
        """
        Execute the query and return the first result.
        
        Returns:
            A model instance or None.
        """
        self.limit(1)
        results = self.all()
        return results[0] if results else None
    
    def count(self) -> int:
        """
        Execute the query and return the count.
        
        Returns:
            The count.
        """
        conn = ConnectionManager.get_default()
        
        # Build the query
        query, params = self._build_query()
        
        # Replace the SELECT clause
        query = query.replace("SELECT *", "SELECT COUNT(*)")
        query = query.replace("SELECT " + ", ".join(f"`{field}`" for field in self.select_fields), "SELECT COUNT(*)")
        
        # Remove the ORDER BY clause
        if " ORDER BY " in query:
            query = query.split(" ORDER BY ")[0]
        
        # Remove the LIMIT and OFFSET clauses
        if " LIMIT " in query:
            query = query.split(" LIMIT ")[0]
        
        if " OFFSET " in query:
            query = query.split(" OFFSET ")[0]
        
        try:
            result = conn.execute(query, params)
        except Exception as e:
            raise QueryError(f"Failed to execute query: {e}")
        
        return result[0][0] if result else 0
