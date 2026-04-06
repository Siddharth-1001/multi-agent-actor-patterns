import asyncio
from typing import Any


class Mailbox:
    """Async FIFO message buffer for an actor."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Any] = asyncio.Queue()

    async def put(self, message: Any) -> None:
        await self._queue.put(message)

    async def get(self) -> Any:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    @property
    def depth(self) -> int:
        return self._queue.qsize()
