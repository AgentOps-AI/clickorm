# ClickORM

A Python ORM framework for ClickHouse with Pydantic integration.

## Features

- Seamless integration with Pydantic for data validation and serialization
- Type-safe query building
- Automatic schema generation and migration
- Support for all ClickHouse data types
- Efficient connection management
- Comprehensive error handling

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

## Documentation

For more detailed documentation, see [the full documentation](https://github.com/AgentOps-AI/clickorm).

## License

MIT
