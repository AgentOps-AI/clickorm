"""
Type definitions for ClickORM.

This module defines the mapping between Python types, Pydantic types, and ClickHouse types.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

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
    return PYTHON_TO_CLICKHOUSE.get(python_type, "String")


def get_python_type(clickhouse_type: str) -> Type:
    """
    Get the Python type for a ClickHouse type.
    
    Args:
        clickhouse_type: The ClickHouse type as a string.
        
    Returns:
        The Python type.
    """
    return CLICKHOUSE_TO_PYTHON.get(clickhouse_type, str)
