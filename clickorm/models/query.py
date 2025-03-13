"""
Query builder for ClickORM.
"""

from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union, TYPE_CHECKING

from clickorm.connection import ConnectionManager
from clickorm.exceptions import QueryError, ValidationError

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from clickorm.models.relationships import Relationship, OneToMany, ManyToOne, ManyToMany
else:
    # Import at runtime
    from clickorm.models.relationships import Relationship, OneToMany, ManyToOne, ManyToMany

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
        
        if self.operator == "IN":
            # Handle IN operator with array
            placeholders = []
            params = {}
            
            for i, val in enumerate(self.value):
                param_key = f"{param_name}_{i}"
                placeholders.append(f"%({param_key})s")
                params[param_key] = val
            
            return f"`{self.field}` IN ({', '.join(placeholders)})", params
        
        elif self.operator == "BETWEEN":
            # Handle BETWEEN operator
            start, end = self.value
            start_param = f"{param_name}_start"
            end_param = f"{param_name}_end"
            
            return f"`{self.field}` BETWEEN %({start_param})s AND %({end_param})s", {
                start_param: start,
                end_param: end
            }
        
        elif self.operator in ("IS NULL", "IS NOT NULL"):
            # Handle IS NULL and IS NOT NULL operators
            return f"`{self.field}` {self.operator}", {}
        
        else:
            # Handle standard operators
            return f"`{self.field}` {self.operator} %({param_name})s", {param_name: self.value}
    
    def __and__(self, other: 'Condition') -> 'CompoundCondition':
        """
        Combine with another condition using AND.
        
        Args:
            other: The other condition.
            
        Returns:
            A CompoundCondition.
        """
        return CompoundCondition(self, "AND", other)
    
    def __or__(self, other: 'Condition') -> 'CompoundCondition':
        """
        Combine with another condition using OR.
        
        Args:
            other: The other condition.
            
        Returns:
            A CompoundCondition.
        """
        return CompoundCondition(self, "OR", other)


class CompoundCondition(Condition):
    """
    Represents a compound query condition (AND/OR).
    """
    
    def __init__(self, left: Condition, operator: str, right: Condition):
        """
        Initialize a new CompoundCondition.
        
        Args:
            left: The left condition.
            operator: The operator (AND/OR).
            right: The right condition.
        """
        self.left = left
        self.operator = operator
        self.right = right
    
    def to_sql(self) -> Tuple[str, Dict[str, Any]]:
        """
        Convert the compound condition to SQL.
        
        Returns:
            A tuple of (sql, params).
        """
        left_sql, left_params = self.left.to_sql()
        right_sql, right_params = self.right.to_sql()
        
        # Merge parameters
        params = {**left_params, **right_params}
        
        # Build SQL
        sql = f"({left_sql} {self.operator} {right_sql})"
        
        return sql, params


class ExistsCondition(Condition):
    """
    Represents an EXISTS condition with a subquery.
    """
    
    def __init__(self, query: str, params: Dict[str, Any]):
        """
        Initialize a new ExistsCondition.
        
        Args:
            query: The subquery.
            params: The parameters for the subquery.
        """
        self.query = query
        self.params = params
    
    def to_sql(self) -> Tuple[str, Dict[str, Any]]:
        """
        Convert the EXISTS condition to SQL.
        
        Returns:
            A tuple of (sql, params).
        """
        return f"EXISTS ({self.query})", self.params


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
        self.joins = []
        self.eager_load = []
    
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
        
    def join(self, model_cls: Type, on: Optional[Condition] = None) -> "Query[T]":
        """
        Add a join to the query.
        
        Args:
            model_cls: The model class to join with.
            on: The join condition. If None, will try to infer from relationships.
            
        Returns:
            The Query instance.
        """
        self.joins.append((model_cls, on))
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
        
        # Handle joins
        for model_cls, on in self.joins:
            if on:
                # Use the explicit join condition
                join_sql, join_params = on.to_sql()
                query += f" JOIN `{model_cls.get_table_name()}` ON {join_sql}"
                params.update(join_params)
            else:
                # Try to infer join condition from relationships
                relationships = self.model_cls.get_relationships()
                
                # Find a relationship to the joined model
                for rel_name, rel in relationships.items():
                    if rel.get_model_cls() == model_cls:
                        # Found a relationship to the joined model
                        if hasattr(rel, "foreign_key") and rel.foreign_key:
                            if isinstance(rel, ManyToOne):
                                # This model has a foreign key to the joined model
                                query += f" JOIN `{model_cls.get_table_name()}` ON `{self.model_cls.get_table_name()}`.`{rel.foreign_key}` = `{model_cls.get_table_name()}`.`{model_cls.get_primary_key_columns()[0].name}`"
                                break
                            elif isinstance(rel, OneToMany):
                                # The joined model has a foreign key to this model
                                query += f" JOIN `{model_cls.get_table_name()}` ON `{self.model_cls.get_table_name()}`.`{self.model_cls.get_primary_key_columns()[0].name}` = `{model_cls.get_table_name()}`.`{rel.foreign_key}`"
                                break
                            elif isinstance(rel, ManyToMany):
                                # This is a many-to-many relationship
                                # We need to join through the junction table
                                query += f" JOIN `{rel.junction_table}` ON `{self.model_cls.get_table_name()}`.`{self.model_cls.get_primary_key_columns()[0].name}` = `{rel.junction_table}`.`{rel.local_key}`"
                                query += f" JOIN `{model_cls.get_table_name()}` ON `{rel.junction_table}`.`{rel.remote_key}` = `{model_cls.get_table_name()}`.`{model_cls.get_primary_key_columns()[0].name}`"
                                break
        
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
    
    def exists(self) -> ExistsCondition:
        """
        Create an EXISTS condition from this query.
        
        Returns:
            An ExistsCondition.
        """
        query, params = self._build_query()
        return ExistsCondition(query, params)
    
    def with_related(self, *relationships: str) -> "Query[T]":
        """
        Eager load related objects.
        
        Args:
            *relationships: The names of relationships to eager load.
            
        Returns:
            The Query instance.
        """
        self.eager_load.extend(relationships)
        return self
        
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
        models = [self.model_cls.from_row(row, columns) for row in result]
        
        # Handle eager loading
        if self.eager_load and models:
            relationships = self.model_cls.get_relationships()
            
            for rel_name in self.eager_load:
                if rel_name in relationships:
                    rel = relationships[rel_name]
                    
                    # Load the relationship for each model
                    for model in models:
                        setattr(model, rel_name, model._load_relationship(rel_name, rel))
        
        return models
    
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
        
    def copy(self) -> "Query[T]":
        """
        Create a copy of this query.
        
        Returns:
            A new Query instance with the same settings.
        """
        query = Query(self.model_cls)
        query.conditions = self.conditions.copy()
        query.order_by_clauses = self.order_by_clauses.copy()
        query.group_by_clauses = self.group_by_clauses.copy()
        query.limit_value = self.limit_value
        query.offset_value = self.offset_value
        query.select_fields = self.select_fields.copy()
        query.joins = self.joins.copy()
        query.eager_load = self.eager_load.copy()
        return query
        
    def paginate(self, page: int = 1, per_page: int = 20) -> Tuple[List[T], int, int, int]:
        """
        Get a page of results.
        
        Args:
            page: The page number (1-indexed).
            per_page: The number of items per page.
            
        Returns:
            A tuple of (items, total, page, pages).
        """
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        count_query = self.copy()
        total = count_query.count()
        
        # Calculate total pages
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        
        # Get items for current page
        self.limit(per_page).offset(offset)
        items = self.all()
        
        return items, total, page, pages
