from __future__ import annotations

import asyncio
from typing import Any

from maap.core.errors import MailboxFullError

# Default maximum mailbox depth to prevent memory exhaustion.
DEFAULT_MAILBOX_CAPACITY: int = 10_000


class Mailbox:
    """Async FIFO message buffer for an actor with bounded capacity.

    Parameters
    ----------
    capacity:
        Maximum number of messages the mailbox can hold. ``0`` means
        unlimited (use with caution). Defaults to ``DEFAULT_MAILBOX_CAPACITY``.
    owner_address:
        Address of the owning actor — used only for error messages.
    """

    def __init__(
        self,
        capacity: int = DEFAULT_MAILBOX_CAPACITY,
        owner_address: str = "<unknown>",
    ) -> None:
        maxsize = capacity if capacity > 0 else 0
        self._queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=maxsize)
        self._capacity = capacity
        self._owner_address = owner_address
        self._total_enqueued: int = 0
        self._total_processed: int = 0

    async def put(self, message: Any) -> None:
        """Enqueue a message.  Raises ``MailboxFullError`` if at capacity."""
        if self._capacity > 0 and self._queue.full():
            raise MailboxFullError(self._owner_address, self._capacity)
        await self._queue.put(message)
        self._total_enqueued += 1

    async def get(self) -> Any:
        msg = await self._queue.get()
        self._total_processed += 1
        return msg

    def task_done(self) -> None:
        self._queue.task_done()

    @property
    def depth(self) -> int:
        return self._queue.qsize()

    @property
    def total_enqueued(self) -> int:
        return self._total_enqueued

    @property
    def total_processed(self) -> int:
        return self._total_processed

    async def drain(self) -> list[Any]:
        """Remove and return all queued messages (used during shutdown)."""
        messages: list[Any] = []
        while not self._queue.empty():
            try:
                messages.append(self._queue.get_nowait())
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break
        return messages
