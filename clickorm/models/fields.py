"""
Custom field types for ClickORM.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pydantic import Field as PydanticField

from clickorm.types import ClickHouseType
from clickorm.exceptions import ValidationError


class Field:
    """
    Field class for ClickORM models.
    
    This class extends Pydantic's Field with ClickHouse-specific functionality.
    """
    
    def __init__(
        self,
        default: Any = None,
        *,
        default_factory: Optional[callable] = None,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        exclude: Optional[Union[bool, callable]] = None,
        include: Optional[Union[bool, callable]] = None,
        const: Optional[bool] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        multiple_of: Optional[float] = None,
        min_items: Optional[int] = None,
        max_items: Optional[int] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        regex: Optional[str] = None,
        clickhouse_type: Optional[ClickHouseType] = None,
        nullable: bool = False,
        low_cardinality: bool = False,
        array: bool = False,
        array_size: Optional[int] = None,
    ):
        """
        Initialize a new Field.
        
        Args:
            default: Default value for the field.
            default_factory: Factory function to generate a default value.
            alias: Alias for the field.
            title: Title for the field.
            description: Description for the field.
            exclude: Whether to exclude the field from serialization.
            include: Whether to include the field in serialization.
            const: Whether the field is constant.
            gt: Greater than validator.
            ge: Greater than or equal validator.
            lt: Less than validator.
            le: Less than or equal validator.
            multiple_of: Multiple of validator.
            min_items: Minimum number of items for arrays.
            max_items: Maximum number of items for arrays.
            min_length: Minimum length for strings.
            max_length: Maximum length for strings.
            regex: Regular expression validator for strings.
            clickhouse_type: ClickHouse type for the field.
            nullable: Whether the field is nullable.
            low_cardinality: Whether to use LowCardinality for the field.
            array: Whether the field is an array.
            array_size: Size of the array if fixed-size.
        """
        self.pydantic_field = PydanticField(
            default=default,
            default_factory=default_factory,
            alias=alias,
            title=title,
            description=description,
            exclude=exclude,
            include=include,
            const=const,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            multiple_of=multiple_of,
            min_items=min_items,
            max_items=max_items,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
        )
        
        self.clickhouse_type = clickhouse_type
        self.nullable = nullable
        self.low_cardinality = low_cardinality
        self.array = array
        self.array_size = array_size
    
    def __call__(self, *args, **kwargs):
        """
        Make the field callable to support Pydantic's field syntax.
        """
        return self.pydantic_field(*args, **kwargs)
        
    def validate(self, value: Any) -> Any:
        """
        Validate a value against the field's constraints.
        
        Args:
            value: The value to validate.
            
        Returns:
            The validated value.
            
        Raises:
            ValidationError: If the value is invalid.
        """
        try:
            # Use Pydantic's validation
            model_field = self.pydantic_field.model_field
            if model_field and hasattr(model_field, "validate"):
                return model_field.validate(value, {}, loc="")
            return value
        except Exception as e:
            raise ValidationError(f"Field validation failed: {e}")
