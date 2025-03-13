"""
Relationship definitions for ClickORM.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, get_args, get_origin

# Use TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from clickorm.models.base import Model

# Use a string type annotation instead of the actual Model class
T = TypeVar('T', bound='Model')


class Relationship(Generic[T]):
    """Base class for all relationships."""
    
    def __init__(self, model_cls: Type[T] | callable, foreign_key: str, backref: Optional[str] = None):
        """
        Initialize a new Relationship.
        
        Args:
            model_cls: The model class or a callable that returns the model class.
                       Using a callable allows for circular references between models.
            foreign_key: The foreign key field name.
            backref: Optional name for the back reference on the related model.
        """
        self.model_cls = model_cls
        self.foreign_key = foreign_key
        self.backref = backref
    
    def get_model_cls(self) -> Type[T]:
        """
        Get the model class, resolving callables if necessary.
        
        Returns:
            The model class.
        """
        if callable(self.model_cls) and not isinstance(self.model_cls, type):
            return self.model_cls()
        return self.model_cls


class OneToMany(Relationship[T]):
    """
    One-to-many relationship.
    
    This relationship is defined on the "one" side and references many related objects.
    For example, an Author has many Books.
    """
    
    def __init__(self, model_cls: Type[T] | callable, foreign_key: str, backref: Optional[str] = None):
        """
        Initialize a new OneToMany relationship.
        
        Args:
            model_cls: The model class or a callable that returns the model class.
            foreign_key: The foreign key field name on the related model.
            backref: Optional name for the back reference on the related model.
        """
        super().__init__(model_cls, foreign_key, backref)


class ManyToOne(Relationship[T]):
    """
    Many-to-one relationship.
    
    This relationship is defined on the "many" side and references one related object.
    For example, a Book has one Author.
    """
    
    def __init__(self, model_cls: Type[T] | callable, foreign_key: str, backref: Optional[str] = None):
        """
        Initialize a new ManyToOne relationship.
        
        Args:
            model_cls: The model class or a callable that returns the model class.
            foreign_key: The foreign key field name on this model.
            backref: Optional name for the back reference on the related model.
        """
        super().__init__(model_cls, foreign_key, backref)


class ManyToMany(Relationship[T]):
    """
    Many-to-many relationship.
    
    This relationship requires a junction table to store the relationships.
    For example, a Student can have many Courses, and a Course can have many Students.
    """
    
    def __init__(
        self, 
        model_cls: Type[T] | callable, 
        junction_table: str, 
        local_key: str, 
        remote_key: str, 
        backref: Optional[str] = None
    ):
        """
        Initialize a new ManyToMany relationship.
        
        Args:
            model_cls: The model class or a callable that returns the model class.
            junction_table: The name of the junction table.
            local_key: The name of the column in the junction table that references this model.
            remote_key: The name of the column in the junction table that references the related model.
            backref: Optional name for the back reference on the related model.
        """
        super().__init__(model_cls, "", backref)
        self.junction_table = junction_table
        self.local_key = local_key
        self.remote_key = remote_key
