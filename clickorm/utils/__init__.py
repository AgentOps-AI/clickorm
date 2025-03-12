"""
Utility functions for ClickORM.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union

T = TypeVar("T")


def to_snake_case(name: str) -> str:
    """
    Convert a string to snake_case.
    
    Args:
        name: The string to convert.
        
    Returns:
        The snake_case string.
    """
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_camel_case(name: str) -> str:
    """
    Convert a string to camelCase.
    
    Args:
        name: The string to convert.
        
    Returns:
        The camelCase string.
    """
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def to_pascal_case(name: str) -> str:
    """
    Convert a string to PascalCase.
    
    Args:
        name: The string to convert.
        
    Returns:
        The PascalCase string.
    """
    return ''.join(x.title() for x in name.split('_'))
