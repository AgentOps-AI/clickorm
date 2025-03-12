"""
Connection management for ClickORM.
"""

import contextlib
from typing import Any, Dict, List, Optional, Tuple, Union

from clickhouse_driver import Client

from clickorm.exceptions import ConnectionError


class ConnectionManager:
    """
    Manages connections to ClickHouse databases.
    
    This class provides a simple interface for connecting to ClickHouse databases
    and executing queries.
    """

    _default_instance = None

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        user: str = "default",
        password: str = "",
        database: str = "default",
        **kwargs: Any,
    ):
        """
        Initialize a new ConnectionManager.
        
        Args:
            host: The ClickHouse server host.
            port: The ClickHouse server port.
            user: The ClickHouse user.
            password: The ClickHouse password.
            database: The ClickHouse database.
            **kwargs: Additional arguments to pass to the ClickHouse client.
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.kwargs = kwargs
        self._client = None

    @property
    def client(self) -> Client:
        """
        Get the ClickHouse client.
        
        Returns:
            The ClickHouse client.
        """
        if self._client is None:
            try:
                self._client = Client(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    **self.kwargs,
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to ClickHouse: {e}")
        return self._client

    def execute(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Tuple]:
        """
        Execute a query.
        
        Args:
            query: The query to execute.
            params: The query parameters.
            
        Returns:
            The query results.
        """
        try:
            return self.client.execute(query, params or {})
        except Exception as e:
            raise ConnectionError(f"Failed to execute query: {e}")

    def execute_iter(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute a query and return an iterator.
        
        Args:
            query: The query to execute.
            params: The query parameters.
            
        Returns:
            An iterator over the query results.
        """
        try:
            return self.client.execute_iter(query, params or {})
        except Exception as e:
            raise ConnectionError(f"Failed to execute query: {e}")

    def execute_with_progress(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Tuple], Any]:
        """
        Execute a query with progress information.
        
        Args:
            query: The query to execute.
            params: The query parameters.
            
        Returns:
            A tuple of (results, progress_info).
        """
        try:
            return self.client.execute_with_progress(query, params or {})
        except Exception as e:
            raise ConnectionError(f"Failed to execute query: {e}")

    @contextlib.contextmanager
    def session(self):
        """
        Create a session context manager.
        
        Yields:
            The ConnectionManager instance.
        """
        try:
            yield self
        finally:
            pass

    @classmethod
    def set_as_default(cls, instance: "ConnectionManager") -> None:
        """
        Set a ConnectionManager instance as the default.
        
        Args:
            instance: The ConnectionManager instance to set as default.
        """
        cls._default_instance = instance

    @classmethod
    def get_default(cls) -> "ConnectionManager":
        """
        Get the default ConnectionManager instance.
        
        Returns:
            The default ConnectionManager instance.
            
        Raises:
            ConnectionError: If no default ConnectionManager has been set.
        """
        if cls._default_instance is None:
            raise ConnectionError("No default ConnectionManager has been set")
        return cls._default_instance
