# ClickORM

A Python ORM framework for ClickHouse with Pydantic integration.

## Features

- Seamless integration with Pydantic for data validation and serialization
- Type-safe query building
- Automatic schema generation and migration
- Support for all ClickHouse data types
- Efficient connection management
- Comprehensive error handling
- Relationship mapping between models

## Installation

```bash
pip install clickorm
```

## Quick Start

```python
from datetime import datetime
from typing import List, Optional
from clickorm import Model, Column, ConnectionManager, types

# Define your model
class User(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    email: str = Column(index=True)
    created_at: datetime = Column(default=datetime.utcnow)
    
    class Meta:
        table_name = "users"
        engine = "MergeTree()"
        order_by = "id"

# Connect to ClickHouse
conn = ConnectionManager(host="localhost", port=9000, database="default")
conn.set_as_default()

# Create the table
User.create_table()

# Insert a user
user = User(name="John Doe", email="john@example.com")
user.save()

# Query users
users = User.query.filter(User.name.like("John%")).all()
for user in users:
    print(f"User: {user.name}, Email: {user.email}")

# Update a user
user.name = "Jane Doe"
user.save()

# Delete a user
user.delete()
```

## Relationship Mapping

ClickORM supports defining relationships between models:

```python
from clickorm import Model, Column
from clickorm.models.relationships import OneToMany, ManyToOne

class Author(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    
    # Define a one-to-many relationship
    books = OneToMany(lambda: Book, foreign_key="author_id")
    
    class Meta:
        table_name = "authors"

class Book(Model):
    id: int = Column(primary_key=True)
    title: str = Column()
    author_id: int = Column(index=True)
    
    # Define a many-to-one relationship
    author = ManyToOne(Author, foreign_key="author_id")
    
    class Meta:
        table_name = "books"
```

You can then use these relationships in queries:

```python
# Eager load relationships
authors = Author.query.with_related("books").all()

# Access related objects
for author in authors:
    print(f"Author: {author.name}")
    for book in author.books:
        print(f"  Book: {book.title}")

# Filter by related objects
books = Book.query.join(Author).filter(Author.name == "John Doe").all()
```

For more advanced relationship mapping, including many-to-many relationships and complex queries, see [the relationships documentation](docs/relationships.md).

## Documentation

For more detailed documentation, see [the full documentation](https://github.com/AgentOps-AI/clickorm).

## License

MIT
