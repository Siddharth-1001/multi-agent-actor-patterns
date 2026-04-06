from __future__ import annotations
import asyncio
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maap.core.system import ActorSystem

from maap.core.mailbox import Mailbox

logger = logging.getLogger(__name__)

ActorAddress = str


class Actor:
    def __init__(self, address: ActorAddress, system: "ActorSystem") -> None:
        self.address: ActorAddress = address
        self._system: ActorSystem = system
        self.mailbox: Mailbox = Mailbox()
        self._running: bool = False
        self._task: asyncio.Task | None = None
        self._supervisor_address: ActorAddress | None = None
        self.state: dict[str, Any] = {}

    async def receive(self, message: Any) -> None:
        raise NotImplementedError

    async def _run(self) -> None:
        self._running = True
        while self._running:
            try:
                message = await self.mailbox.get()
                try:
                    await self.receive(message)
                except Exception as exc:
                    logger.exception(
                        "Actor %s raised exception processing message %r",
                        self.address,
                        message,
                    )
                    await self._system._handle_actor_failure(self, exc, message)
                finally:
                    self.mailbox.task_done()
            except asyncio.CancelledError:
                break

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def tell(self, message: Any) -> None:
        await self.mailbox.put(message)
