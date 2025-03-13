"""
Type definitions for ClickORM.

This module defines the mapping between Python types, Pydantic types, and ClickHouse types.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, get_args, get_origin, TypeVar

# Define ClickHouseType as a TypeVar that can be any string
ClickHouseType = TypeVar('ClickHouseType', bound=str)

# Basic types
Int8 = int
Int16 = int
Int32 = int
Int64 = int
UInt8 = int
UInt16 = int
UInt32 = int
UInt64 = int
Float32 = float
Float64 = float
String = str
FixedString = str
UUID = str
IPv4 = str
IPv6 = str
Boolean = bool

# Date and time types
Date = date
Date32 = date
DateTime = datetime
DateTime64 = datetime

# Complex types
Array = List
Nullable = Optional
LowCardinality = Any
Map = Dict
Tuple = Tuple
Enum8 = Enum
Enum16 = Enum

# Specialized types
Decimal32 = Decimal
Decimal64 = Decimal
Decimal128 = Decimal
Decimal256 = Decimal

# Type mapping from Python to ClickHouse
PYTHON_TO_CLICKHOUSE = {
    int: "Int32",
    float: "Float64",
    str: "String",
    bool: "UInt8",
    date: "Date",
    datetime: "DateTime",
    list: "Array",
    dict: "Map",
    tuple: "Tuple",
    Decimal: "Decimal64",
    set: "Array",
    # Complex types
    List[str]: "Array(String)",
    List[int]: "Array(Int32)",
    List[float]: "Array(Float64)",
    List[bool]: "Array(UInt8)",
    Dict[str, str]: "Map(String, String)",
    Dict[str, int]: "Map(String, Int32)",
    Dict[str, float]: "Map(String, Float64)",
    Dict[str, Any]: "Map(String, String)",
    Dict[int, str]: "Map(Int32, String)",
    Dict[int, int]: "Map(Int32, Int32)",
}

# Type mapping from ClickHouse to Python
CLICKHOUSE_TO_PYTHON = {
    "Int8": int,
    "Int16": int,
    "Int32": int,
    "Int64": int,
    "UInt8": int,
    "UInt16": int,
    "UInt32": int,
    "UInt64": int,
    "Float32": float,
    "Float64": float,
    "String": str,
    "FixedString": str,
    "UUID": str,
    "IPv4": str,
    "IPv6": str,
    "Date": date,
    "Date32": date,
    "DateTime": datetime,
    "DateTime64": datetime,
    "Array": list,
    "Map": dict,
    "Tuple": tuple,
    "Decimal32": Decimal,
    "Decimal64": Decimal,
    "Decimal128": Decimal,
    "Decimal256": Decimal,
    "Enum8": Enum,
    "Enum16": Enum,
}


def get_clickhouse_type(python_type: Type) -> str:
    """
    Get the ClickHouse type for a Python type.
    
    Args:
        python_type: The Python type.
        
    Returns:
        The ClickHouse type as a string.
    """
    # Check if the type is directly in the mapping
    if python_type in PYTHON_TO_CLICKHOUSE:
        return PYTHON_TO_CLICKHOUSE[python_type]
    
    # Handle generic types
    origin = get_origin(python_type)
    args = get_args(python_type)
    
    if origin is list or origin is List:
        # Handle List[T]
        if args:
            element_type = get_clickhouse_type(args[0])
            return f"Array({element_type})"
        return "Array(String)"
    
    elif origin is dict or origin is Dict:
        # Handle Dict[K, V]
        if len(args) == 2:
            key_type = get_clickhouse_type(args[0])
            value_type = get_clickhouse_type(args[1])
            return f"Map({key_type}, {value_type})"
        return "Map(String, String)"
    
    elif origin is tuple or origin is Tuple:
        # Handle Tuple[T1, T2, ...]
        if args:
            element_types = [get_clickhouse_type(arg) for arg in args]
            return f"Tuple({', '.join(element_types)})"
        return "Tuple(String)"
    
    elif origin is Union:
        # Handle Union[T, None] (Optional[T])
        if type(None) in args:
            # This is an Optional[T]
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return f"Nullable({get_clickhouse_type(non_none_args[0])})"
        return "String"
    
    # Default to String for unknown types
    return "String"


def get_python_type(clickhouse_type: str) -> Type:
    """
    Get the Python type for a ClickHouse type.
    
    Args:
        clickhouse_type: The ClickHouse type as a string.
        
    Returns:
        The Python type.
    """
    return CLICKHOUSE_TO_PYTHON.get(clickhouse_type, str)
