"""
Basic usage example for ClickORM.
"""

from datetime import datetime
from typing import List, Optional

from clickorm import Model, Column, ConnectionManager, Field


# Connect to ClickHouse
conn = ConnectionManager(
    host="localhost",
    port=9000,
    user="default",
    password="",
    database="default",
)
ConnectionManager.set_as_default(conn)


# Define a model
class User(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    email: str = Column(index=True)
    created_at: datetime = Column(default=datetime.utcnow)
    
    class Meta:
        table_name = "users"
        engine = "MergeTree()"
        order_by = "id"


# Create the table
User.create_table()


# Create a user
user = User(id=1, name="John Doe", email="john@example.com")
user.save()


# Query users
users = User.query.filter(User.name == "John Doe").all()
for user in users:
    print(f"User: {user.name} ({user.email})")


# Update a user
user.name = "Jane Doe"
user.save()


# Delete a user
user.delete()


# Using Pydantic Field for advanced validation
class Product(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    price: float = Column()
    description: Optional[str] = Column(default=None)
    tags: List[str] = Column(default_factory=list)
    
    # Using Field for advanced validation
    stock: int = Column(field=Field(ge=0, description="Stock must be non-negative"))
    
    class Meta:
        table_name = "products"
        engine = "MergeTree()"
        order_by = "id"


# Create the table
Product.create_table()


# Create a product
product = Product(
    id=1,
    name="Laptop",
    price=999.99,
    description="A powerful laptop",
    tags=["electronics", "computers"],
    stock=10,
)
product.save()


# Query products
products = Product.query.filter(Product.price < 1000).all()
for product in products:
    print(f"Product: {product.name} (${product.price})")
