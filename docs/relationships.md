# Relationship Mapping in ClickORM

ClickORM provides powerful relationship mapping capabilities that allow you to define and work with relationships between models. This document explains how to define and use relationships in your ClickORM models.

## Relationship Types

ClickORM supports three types of relationships:

1. **OneToMany**: A one-to-many relationship where one model has many related models.
2. **ManyToOne**: A many-to-one relationship where many models are related to one model.
3. **ManyToMany**: A many-to-many relationship where many models are related to many models through a junction table.

## Defining Relationships

### One-to-Many Relationship

A one-to-many relationship is defined on the "one" side of the relationship:

```python
from clickorm import Model, Column
from clickorm.models.relationships import OneToMany

class Author(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    
    # Define a one-to-many relationship
    books = OneToMany(lambda: Book, foreign_key="author_id")
    
    class Meta:
        table_name = "authors"
```

The `foreign_key` parameter specifies the name of the column in the related model that references this model.

### Many-to-One Relationship

A many-to-one relationship is defined on the "many" side of the relationship:

```python
from clickorm import Model, Column
from clickorm.models.relationships import ManyToOne

class Book(Model):
    id: int = Column(primary_key=True)
    title: str = Column()
    author_id: int = Column(index=True)
    
    # Define a many-to-one relationship
    author = ManyToOne(Author, foreign_key="author_id")
    
    class Meta:
        table_name = "books"
```

The `foreign_key` parameter specifies the name of the column in this model that references the related model.

### Many-to-Many Relationship

A many-to-many relationship requires a junction table to store the relationships:

```python
from clickorm import Model, Column
from clickorm.models.relationships import ManyToMany

class Student(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    
    # Define a many-to-many relationship
    courses = ManyToMany(
        lambda: Course,
        junction_table="student_courses",
        local_key="student_id",
        remote_key="course_id"
    )
    
    class Meta:
        table_name = "students"

class Course(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    
    # Define the other side of the many-to-many relationship
    students = ManyToMany(
        Student,
        junction_table="student_courses",
        local_key="course_id",
        remote_key="student_id"
    )
    
    class Meta:
        table_name = "courses"
```

The `junction_table` parameter specifies the name of the junction table, and the `local_key` and `remote_key` parameters specify the names of the columns in the junction table that reference this model and the related model, respectively.

## Using Relationships

### Eager Loading

You can eager load relationships using the `with_related` method:

```python
# Eager load books for all authors
authors = Author.query.with_related("books").all()

# Access the related books
for author in authors:
    print(f"Author: {author.name}")
    for book in author.books:
        print(f"  Book: {book.title}")
```

### Filtering by Related Models

You can filter by related models using the `join` method:

```python
# Find all books by authors with a specific name
books = Book.query.join(Author).filter(Author.name == "John Doe").all()

# Find all authors with books published after a certain date
authors = Author.query.join(Book).filter(Book.published_date > datetime(2020, 1, 1)).all()
```

### Accessing Related Models

Once you have loaded a model with its relationships, you can access the related models as attributes:

```python
# Get a book
book = Book.query.first()

# Access the related author
author = book.author
print(f"Author: {author.name}")

# Get an author
author = Author.query.first()

# Access the related books
for book in author.books:
    print(f"Book: {book.title}")
```

## Circular References

When you have circular references between models, you can use a lambda function to defer the resolution of the model class:

```python
class Parent(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    
    # Use a lambda to avoid circular reference
    children = OneToMany(lambda: Child, foreign_key="parent_id")
    
    class Meta:
        table_name = "parents"

class Child(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    parent_id: int = Column(index=True)
    
    # Reference to Parent is direct since it's already defined
    parent = ManyToOne(Parent, foreign_key="parent_id")
    
    class Meta:
        table_name = "children"
```

## Performance Considerations

When working with relationships in ClickHouse, keep in mind that ClickHouse is optimized for analytical queries rather than relational operations. Here are some tips for optimizing performance:

1. **Use eager loading**: Always use `with_related` to load related models in a single query rather than making multiple queries.
2. **Limit the number of joins**: ClickHouse's join performance can be slower than traditional relational databases, so try to minimize the number of joins in your queries.
3. **Use denormalized data**: Consider denormalizing your data to avoid joins altogether when possible.
4. **Use materialized views**: ClickHouse's materialized views can be used to precompute joins and aggregations.

## Example: Trace and Span Relationship

Here's a complete example of defining and using relationships between Trace and Span models:

```python
from clickorm import Model, Column
from clickorm.models.relationships import OneToMany, ManyToOne

class Trace(Model):
    trace_id: str = Column(primary_key=True)
    
    # Define a one-to-many relationship to spans
    spans = OneToMany(lambda: Span, foreign_key="trace_id")
    
    class Meta:
        table_name = "otel_traces"
        database = "otel"
        engine = "MergeTree()"
        order_by = "trace_id"
    
    @property
    def root_span(self):
        """Get the root span of the trace."""
        if not hasattr(self, "_spans") or not self._spans:
            return None
        
        # Find the span with no parent
        for span in self._spans:
            if not span.parent_span_id:
                return span
        
        # If no span has a null parent, return the first span
        return self._spans[0] if self._spans else None

class Span(Model):
    span_id: str = Column(primary_key=True)
    trace_id: str = Column(index=True)
    parent_span_id: Optional[str] = Column(nullable=True)
    span_name: str = Column()
    
    # Define a many-to-one relationship to trace
    trace = ManyToOne(Trace, foreign_key="trace_id")
    
    class Meta:
        table_name = "otel_spans"
        database = "otel"
        engine = "MergeTree()"
        order_by = "span_id"

# Query traces with spans
traces = Trace.query.with_related("spans").all()

# Access spans for a trace
for trace in traces:
    print(f"Trace: {trace.trace_id}")
    for span in trace.spans:
        print(f"  Span: {span.span_name}")

# Query spans with their traces
spans = Span.query.with_related("trace").all()

# Access the trace for a span
for span in spans:
    print(f"Span: {span.span_name}")
    print(f"  Trace: {span.trace.trace_id}")

# Filter spans by trace properties
spans = Span.query.join(Trace).filter(Trace.trace_id == "abc123").all()
```

This example demonstrates how to define and use relationships between Trace and Span models, which is a common pattern in distributed tracing systems.
