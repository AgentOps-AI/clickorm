"""
Example implementation of AgentOps.Next trace API using ClickORM.

This example demonstrates how the v4 API could be refactored using ClickORM
to simplify complex database interactions while maintaining type safety.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from fastapi import APIRouter, HTTPException, Query, Path, status
from pydantic import BaseModel

from clickorm import Model, Column, ConnectionManager
from clickorm.models.fields import Field
from clickorm.models.relationships import OneToMany, ManyToOne


# Define models
class Span(Model):
    """
    Represents a span in a trace.
    
    A span represents a unit of work or operation in a distributed system.
    """
    
    span_id: str = Column(primary_key=True)
    trace_id: str = Column(index=True)
    parent_span_id: Optional[str] = Column(nullable=True)
    span_name: str = Column()
    span_kind: str = Column()
    service_name: str = Column()
    start_time: datetime = Column()
    end_time: datetime = Column()
    status_code: str = Column()
    status_message: Optional[str] = Column(nullable=True)
    attributes: Dict[str, Any] = Column(default_factory=dict)
    resource_attributes: Dict[str, Any] = Column(default_factory=dict)
    session_id: Optional[str] = Column(nullable=True, index=True)
    
    # Define relationships
    trace = ManyToOne(lambda: Trace, foreign_key="trace_id")
    
    class Meta:
        table_name = "otel_spans"
        database = "otel"
        engine = "MergeTree()"
        order_by = "span_id"


class Event(Model):
    """
    Represents an event in a span.
    
    Events are time-stamped annotations within a span.
    """
    
    event_id: str = Column(primary_key=True)
    span_id: str = Column(index=True)
    trace_id: str = Column(index=True)
    name: str = Column()
    timestamp: datetime = Column()
    attributes: Dict[str, Any] = Column(default_factory=dict)
    
    # Define relationships
    span = ManyToOne(Span, foreign_key="span_id")
    
    class Meta:
        table_name = "otel_events"
        database = "otel"
        engine = "MergeTree()"
        order_by = "event_id"


class Link(Model):
    """
    Represents a link between spans.
    
    Links are references from one span to another.
    """
    
    link_id: str = Column(primary_key=True)
    span_id: str = Column(index=True)
    trace_id: str = Column(index=True)
    linked_span_id: str = Column()
    linked_trace_id: str = Column()
    attributes: Dict[str, Any] = Column(default_factory=dict)
    
    # Define relationships
    span = ManyToOne(Span, foreign_key="span_id")
    
    class Meta:
        table_name = "otel_links"
        database = "otel"
        engine = "MergeTree()"
        order_by = "link_id"


class Trace(Model):
    """
    Represents a trace.
    
    A trace is a collection of spans that form a tree-like structure.
    """
    
    trace_id: str = Column(primary_key=True)
    
    # Define relationships
    spans = OneToMany(Span, foreign_key="trace_id")
    
    class Meta:
        table_name = "otel_traces"
        database = "otel"
        engine = "MergeTree()"
        order_by = "trace_id"
    
    @property
    def root_span(self) -> Optional[Span]:
        """
        Get the root span of the trace.
        
        Returns:
            The root span or None if no spans exist.
        """
        if not hasattr(self, "_spans") or not self._spans:
            return None
        
        # Find the span with no parent
        for span in self._spans:
            if not span.parent_span_id:
                return span
        
        # If no span has a null parent, return the first span
        return self._spans[0] if self._spans else None
    
    @property
    def root_service_name(self) -> str:
        """
        Get the root service name.
        
        Returns:
            The root service name or an empty string if no root span exists.
        """
        root = self.root_span
        return root.service_name if root else ""
    
    @property
    def root_span_name(self) -> str:
        """
        Get the root span name.
        
        Returns:
            The root span name or an empty string if no root span exists.
        """
        root = self.root_span
        return root.span_name if root else ""
    
    @property
    def start_time(self) -> datetime:
        """
        Get the start time of the trace.
        
        Returns:
            The start time or datetime.min if no spans exist.
        """
        if not hasattr(self, "_spans") or not self._spans:
            return datetime.min
        return min(span.start_time for span in self._spans)
    
    @property
    def end_time(self) -> datetime:
        """
        Get the end time of the trace.
        
        Returns:
            The end time or datetime.max if no spans exist.
        """
        if not hasattr(self, "_spans") or not self._spans:
            return datetime.max
        return max(span.end_time for span in self._spans)
    
    @property
    def duration(self) -> int:
        """
        Get the duration of the trace in milliseconds.
        
        Returns:
            The duration in milliseconds.
        """
        return int((self.end_time - self.start_time).total_seconds() * 1000)
    
    @property
    def span_count(self) -> int:
        """
        Get the number of spans in the trace.
        
        Returns:
            The number of spans.
        """
        return len(self._spans) if hasattr(self, "_spans") else 0
    
    @property
    def error_count(self) -> int:
        """
        Get the number of spans with an error status.
        
        Returns:
            The number of spans with an error status.
        """
        if not hasattr(self, "_spans") or not self._spans:
            return 0
        return sum(1 for span in self._spans if span.status_code == "ERROR")


# Response models
class TraceListItem(BaseModel):
    """Response model for a trace in a list."""
    
    trace_id: str
    root_service_name: str
    root_span_name: str
    start_time: str
    end_time: str
    duration: int
    span_count: int
    error_count: int


class TraceListResponse(BaseModel):
    """Response model for a list of traces."""
    
    traces: List[TraceListItem]
    total: int
    limit: int
    offset: int


class SpanListItem(BaseModel):
    """Response model for a span in a list."""
    
    span_id: str
    parent_span_id: Optional[str]
    span_name: str
    span_kind: str
    service_name: str
    start_time: str
    end_time: str
    duration: int
    status_code: str
    status_message: Optional[str]
    attributes: Dict[str, Any]
    resource_attributes: Dict[str, Any]


class TraceDetailResponse(BaseModel):
    """Response model for a trace detail."""
    
    trace_id: str
    root_service_name: str
    root_span_name: str
    start_time: str
    end_time: str
    duration: int
    span_count: int
    error_count: int
    spans: List[SpanListItem]


# Create router
router = APIRouter(prefix="/traces", tags=["traces"])


@router.get("", response_model=TraceListResponse)
async def get_traces(
    session_id: Optional[str] = None,
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    service_name: Optional[str] = Query(None),
    span_name: Optional[str] = Query(None),
    status_code: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get a list of traces with filtering and pagination.
    
    Args:
        session_id: Filter by session ID.
        start_time: Filter by start time (ISO format).
        end_time: Filter by end time (ISO format).
        service_name: Filter by service name.
        span_name: Filter by span name.
        status_code: Filter by status code.
        limit: Maximum number of traces to return.
        offset: Number of traces to skip.
        
    Returns:
        A TraceListResponse with the traces and pagination info.
    """
    try:
        # Build query
        query = Trace.query
        
        # Apply filters to spans
        span_filters = []
        if session_id:
            span_filters.append(Span.session_id == session_id)
        if start_time:
            span_filters.append(Span.start_time >= datetime.fromisoformat(start_time.replace('Z', '+00:00')))
        if end_time:
            span_filters.append(Span.end_time <= datetime.fromisoformat(end_time.replace('Z', '+00:00')))
        if service_name: 
            span_filters.append(Span.service_name == service_name)
        if span_name:
            span_filters.append(Span.span_name == span_name)
        if status_code:
            span_filters.append(Span.status_code == status_code)
        
        # Get trace IDs matching the span filters
        if span_filters:
            span_query = Span.query.filter(*span_filters)
            trace_ids = [span.trace_id for span in span_query.all()]
            query = query.filter(Trace.trace_id.in_(trace_ids))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query with eager loading of spans
        traces = query.with_related("spans").all()
        
        # Format response
        trace_items = []
        for trace in traces:
            trace_items.append(TraceListItem(
                trace_id=trace.trace_id,
                root_service_name=trace.root_service_name,
                root_span_name=trace.root_span_name,
                start_time=trace.start_time.isoformat(),
                end_time=trace.end_time.isoformat(),
                duration=trace.duration,
                span_count=trace.span_count,
                error_count=trace.error_count
            ))
        
        return TraceListResponse(
            traces=trace_items,
            total=total,
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Unexpected error", "message": str(e)}
        )


@router.get("/{trace_id}", response_model=TraceDetailResponse)
async def get_trace(
    trace_id: str = Path(..., description="The trace ID")
):
    """
    Get a trace by ID.
    
    Args:
        trace_id: The trace ID.
        
    Returns:
        A TraceDetailResponse with the trace details.
    """
    try:
        # Get the trace with spans
        trace = Trace.query.filter(Trace.trace_id == trace_id).with_related("spans").first()
        
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Trace not found", "message": f"Trace with ID {trace_id} not found"}
            )
        
        # Format spans
        span_items = []
        for span in trace._spans:
            duration = int((span.end_time - span.start_time).total_seconds() * 1000)
            span_items.append(SpanListItem(
                span_id=span.span_id,
                parent_span_id=span.parent_span_id,
                span_name=span.span_name,
                span_kind=span.span_kind,
                service_name=span.service_name,
                start_time=span.start_time.isoformat(),
                end_time=span.end_time.isoformat(),
                duration=duration,
                status_code=span.status_code,
                status_message=span.status_message,
                attributes=span.attributes,
                resource_attributes=span.resource_attributes
            ))
        
        # Format response
        return TraceDetailResponse(
            trace_id=trace.trace_id,
            root_service_name=trace.root_service_name,
            root_span_name=trace.root_span_name,
            start_time=trace.start_time.isoformat(),
            end_time=trace.end_time.isoformat(),
            duration=trace.duration,
            span_count=trace.span_count,
            error_count=trace.error_count,
            spans=span_items
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Unexpected error", "message": str(e)}
        )
