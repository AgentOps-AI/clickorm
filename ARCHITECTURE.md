# ClickORM Architecture

## Overview

ClickORM is a Python ORM framework designed to interoperate with Pydantic and ClickHouse. It provides a simple, intuitive interface for defining models, executing queries, and managing database connections.

## Core Components

### 1. Model Definition

Models are defined using Pydantic's BaseModel, with additional metadata for ClickHouse-specific features:

```python
from clickorm import Model, Column, types

class User(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    email: str = Column(index=True)
    created_at: datetime = Column(default=datetime.utcnow)
    
    class Meta:
        table_name = "users"
        engine = "MergeTree()"
        order_by = "id"
```

### 2. Connection Management

Connection management is handled by a dedicated class that wraps the ClickHouse driver:

```python
from clickorm import ConnectionManager

# Create a connection manager
conn = ConnectionManager(host="localhost", port=9000, database="default")

# Use the connection
with conn.session() as session:
    users = session.query(User).filter(User.id > 10).all()
```

### 3. Query Building

Queries are built using a fluent interface similar to SQLAlchemy:

```python
# Select query
users = User.query.filter(User.name.like("John%")).order_by(User.created_at.desc()).limit(10).all()

# Insert
user = User(name="John Doe", email="john@example.com")
user.save()

# Update
user.name = "Jane Doe"
user.save()

# Delete
user.delete()
```

### 4. Type Conversion

ClickORM handles type conversion between Python, Pydantic, and ClickHouse:

| Python Type | Pydantic Type | ClickHouse Type |
|-------------|---------------|----------------|
| int         | int           | Int32/Int64    |
| float       | float         | Float32/Float64|
| str         | str           | String         |
| datetime    | datetime      | DateTime       |
| date        | date          | Date           |
| list        | List[T]       | Array(T)       |
| dict        | Dict[K, V]    | Map(K, V)      |

### 5. Schema Management

Schema management includes creating, altering, and dropping tables:

```python
# Create table
User.create_table()

# Drop table
User.drop_table()

# Alter table
User.alter_table(add_column=Column("new_field", str))
```

### 6. Error Handling

Error handling is provided through custom exceptions:

- `ConnectionError`: Connection-related errors
- `QueryError`: Query-related errors
- `ValidationError`: Model validation errors
- `SchemaError`: Schema-related errors

## Architecture Diagram

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  Pydantic Model  |     |  ClickORM Model  |     | ClickHouse Driver|
|                  |     |                  |     |                  |
+--------+---------+     +--------+---------+     +--------+---------+
         ^                        ^                        ^
         |                        |                        |
         |                        |                        |
         |                        |                        |
+--------+---------+     +--------+---------+     +--------+---------+
|                  |     |                  |     |                  |
| Type Conversion  |<--->|  Query Builder   |<--->|   Connection     |
|                  |     |                  |     |   Manager        |
+------------------+     +------------------+     +------------------+
```

## Implementation Plan

1. Core Model Definition
2. Connection Management
3. Query Building
4. Type Conversion
5. Schema Management
6. Error Handling
7. Testing and Documentation
