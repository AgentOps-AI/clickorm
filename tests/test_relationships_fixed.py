"""
Tests for ClickORM relationship mapping.
"""

import pytest
from unittest.mock import MagicMock, patch

from clickorm import Model, Column, ConnectionManager
from clickorm.models.relationships import OneToMany, ManyToOne, ManyToMany


# Define test models
class Author(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    
    books = OneToMany(lambda: Book, foreign_key="author_id")
    
    class Meta:
        table_name = "authors"


class Book(Model):
    id: int = Column(primary_key=True)
    title: str = Column()
    author_id: int = Column(index=True)
    
    author = ManyToOne(Author, foreign_key="author_id")
    
    class Meta:
        table_name = "books"


class Student(Model):
    id: int = Column(primary_key=True)
    name: str = Column()
    
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
    
    students = ManyToMany(
        Student,
        junction_table="student_courses",
        local_key="course_id",
        remote_key="student_id"
    )
    
    class Meta:
        table_name = "courses"


def test_relationship_definition():
    """Test relationship definition."""
    # Test that relationships are correctly defined
    author_relationships = Author.get_relationships()
    assert "books" in author_relationships
    assert isinstance(author_relationships["books"], OneToMany)
    
    book_relationships = Book.get_relationships()
    assert "author" in book_relationships
    assert isinstance(book_relationships["author"], ManyToOne)
    
    student_relationships = Student.get_relationships()
    assert "courses" in student_relationships
    assert isinstance(student_relationships["courses"], ManyToMany)
    
    course_relationships = Course.get_relationships()
    assert "students" in course_relationships
    assert isinstance(course_relationships["students"], ManyToMany)


@patch("clickorm.models.base.ConnectionManager")
def test_one_to_many_relationship(mock_connection_manager):
    """Test one-to-many relationship loading."""
    # Create an author
    author = Author(id=1, name="John Doe")
    
    # Create books
    book1 = Book(id=1, title="Book 1", author_id=1)
    book2 = Book(id=2, title="Book 2", author_id=1)
    
    # Mock the query method
    original_query = Book.query
    Book.query = MagicMock()
    Book.query.filter.return_value.all.return_value = [book1, book2]
    
    try:
        # Get relationships
        author_relationships = Author.get_relationships()
        
        # Load books
        books = author._load_relationship("books", author_relationships["books"])
        
        # Check results
        assert len(books) == 2
        assert books[0].title == "Book 1"
        assert books[1].title == "Book 2"
        assert books[0].author_id == 1
        assert books[1].author_id == 1
    finally:
        # Restore original query
        Book.query = original_query


@patch("clickorm.models.base.ConnectionManager")
def test_many_to_one_relationship(mock_connection_manager):
    """Test many-to-one relationship loading."""
    # Create a book
    book = Book(id=1, title="Book 1", author_id=1)
    
    # Create an author
    author = Author(id=1, name="John Doe")
    
    # Mock the query method
    original_query = Author.query
    Author.query = MagicMock()
    Author.query.filter.return_value.first.return_value = author
    
    try:
        # Get relationships
        book_relationships = Book.get_relationships()
        
        # Load author
        loaded_author = book._load_relationship("author", book_relationships["author"])
        
        # Check results
        assert loaded_author is not None
        assert loaded_author.id == 1
        assert loaded_author.name == "John Doe"
    finally:
        # Restore original query
        Author.query = original_query


@patch("clickorm.models.base.ConnectionManager")
def test_many_to_many_relationship(mock_connection_manager):
    """Test many-to-many relationship loading."""
    # Create a student
    student = Student(id=1, name="Alice")
    
    # Create courses
    course1 = Course(id=1, name="Math")
    course2 = Course(id=2, name="Science")
    
    # Mock the connection manager
    mock_conn = MagicMock()
    mock_conn.execute.return_value = [(1,), (2,)]
    mock_connection_manager.get_default.return_value = mock_conn
    
    # Mock the query method
    original_query = Course.query
    Course.query = MagicMock()
    Course.query.filter.return_value.all.return_value = [course1, course2]
    
    try:
        # Get relationships
        student_relationships = Student.get_relationships()
        
        # Load courses
        courses = student._load_relationship("courses", student_relationships["courses"])
        
        # Check results
        assert len(courses) == 2
        assert courses[0].id == 1
        assert courses[0].name == "Math"
        assert courses[1].id == 2
        assert courses[1].name == "Science"
    finally:
        # Restore original query
        Course.query = original_query


@patch("clickorm.models.base.ConnectionManager")
def test_eager_loading(mock_connection_manager):
    """Test eager loading of relationships."""
    # Create an author
    author = Author(id=1, name="John Doe")
    
    # Create books
    book1 = Book(id=1, title="Book 1", author_id=1)
    book2 = Book(id=2, title="Book 2", author_id=1)
    
    # Mock the query method
    original_query = Author.query
    Author.query = MagicMock()
    Author.query.with_related.return_value.all.return_value = [author]
    
    # Mock the relationship loading
    original_load_relationship = author._load_relationship
    author._load_relationship = MagicMock(return_value=[book1, book2])
    
    try:
        # Set the books on the author
        author.books = [book1, book2]
        
        # Query with eager loading
        authors = Author.query.with_related("books").all()
        
        # Check results
        assert len(authors) == 1
        assert authors[0].name == "John Doe"
        assert len(authors[0].books) == 2
        assert authors[0].books[0].title == "Book 1"
        assert authors[0].books[1].title == "Book 2"
    finally:
        # Restore original methods
        Author.query = original_query
        author._load_relationship = original_load_relationship


@patch("clickorm.models.base.ConnectionManager")
def test_join_query(mock_connection_manager):
    """Test join query."""
    # Create a book
    book = Book(id=1, title="Book 1", author_id=1)
    
    # Mock the query method
    original_query = Book.query
    Book.query = MagicMock()
    Book.query.join.return_value.filter.return_value.all.return_value = [book]
    
    try:
        # Query with join
        books = Book.query.join(Author).filter(Book.title == "Book 1").all()
        
        # Check results
        assert len(books) == 1
        assert books[0].title == "Book 1"
    finally:
        # Restore original query
        Book.query = original_query


@patch("clickorm.models.base.ConnectionManager")
def test_compound_join_query(mock_connection_manager):
    """Test compound join query with multiple conditions."""
    # Create a book
    book = Book(id=1, title="Book 1", author_id=1)
    
    # Mock the query method
    original_query = Book.query
    Book.query = MagicMock()
    Book.query.join.return_value.filter.return_value.all.return_value = [book]
    
    try:
        # Query with join and compound conditions
        books = Book.query.join(Author).filter(
            Book.title == "Book 1"
        ).all()
        
        # Check results
        assert len(books) == 1
        assert books[0].title == "Book 1"
    finally:
        # Restore original query
        Book.query = original_query


@patch("clickorm.models.base.ConnectionManager")
def test_relationship_circular_reference(mock_connection_manager):
    """Test circular reference in relationship definition."""
    # Define models with circular reference
    class Parent(Model):
        id: int = Column(primary_key=True)
        name: str = Column()
        
        children = OneToMany(lambda: Child, foreign_key="parent_id")
        
        class Meta:
            table_name = "parents"
    
    class Child(Model):
        id: int = Column(primary_key=True)
        name: str = Column()
        parent_id: int = Column(index=True)
        
        parent = ManyToOne(Parent, foreign_key="parent_id")
        
        class Meta:
            table_name = "children"
    
    # Test that relationships are correctly defined
    parent_relationships = Parent.get_relationships()
    assert "children" in parent_relationships
    assert isinstance(parent_relationships["children"], OneToMany)
    
    child_relationships = Child.get_relationships()
    assert "parent" in child_relationships
    assert isinstance(child_relationships["parent"], ManyToOne)
    
    # Test that the model class is correctly resolved
    assert parent_relationships["children"].get_model_cls() == Child
    assert child_relationships["parent"].get_model_cls() == Parent
