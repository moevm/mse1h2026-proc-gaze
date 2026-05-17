import asyncio
from typing import Generic, TypeVar

T = TypeVar("T")

class ConnectionManager(Generic[T]):
    def __init__(self):
        self._connections = []
        self._lock = asyncio.Lock()

    async def add_connection(self, connection: asyncio.Queue):
        async with self._lock:
            self._connections.append(connection)

    async def remove_connection(self, connection: asyncio.Queue):
        async with self._lock:
            self._connections.remove(connection)

    async def broadcast(self, message: T):
        broken_connections = []
        async with self._lock:
            for conn in self._connections:
                try:
                    await conn.put(message)
                except Exception:
                    broken_connections.append(conn)
            for conn in broken_connections:
                self._connections.remove(conn)