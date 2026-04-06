from __future__ import annotations

import asyncio
import contextlib
import logging
import re
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maap.core.system import ActorSystem

from maap.core.errors import InvalidAddressError, MailboxFullError
from maap.core.mailbox import DEFAULT_MAILBOX_CAPACITY, Mailbox

logger = logging.getLogger(__name__)

ActorAddress = str

# Allowed characters in actor addresses: alphanumeric, hyphens, underscores, dots.
_ADDRESS_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,254}$")


def validate_address(address: str) -> None:
    """Validate that an actor address is safe and well-formed."""
    if not isinstance(address, str):
        raise InvalidAddressError(str(address), "must be a string")
    if not _ADDRESS_RE.match(address):
        raise InvalidAddressError(
            address,
            "must be 1-255 chars, start with alphanumeric, contain only [a-zA-Z0-9._-]",
        )


class Actor:
    """Base class for all actors in the system.

    Subclasses must implement ``receive(message)`` to handle incoming messages.

    Lifecycle hooks (override as needed):
        - ``pre_start``  : called once before the message loop begins.
        - ``post_stop``  : called once after the message loop exits.
        - ``pre_restart``: called on the *old* instance before it is replaced.
    """

    # Subclasses can override to set a custom mailbox capacity.
    mailbox_capacity: int = DEFAULT_MAILBOX_CAPACITY

    def __init__(self, address: ActorAddress, system: ActorSystem) -> None:
        validate_address(address)
        self.address: ActorAddress = address
        self._system: ActorSystem = system
        self.mailbox: Mailbox = Mailbox(
            capacity=self.mailbox_capacity,
            owner_address=address,
        )
        self._running: bool = False
        self._task: asyncio.Task[None] | None = None
        self._supervisor_address: ActorAddress | None = None
        self.state: dict[str, Any] = {}
        self._created_at: float = time.monotonic()
        self._message_count: int = 0

    # -- Lifecycle hooks (override in subclasses) --

    async def pre_start(self) -> None:
        """Called once before the actor begins processing messages."""

    async def post_stop(self) -> None:
        """Called once after the actor's message loop exits."""

    async def pre_restart(self, reason: Exception | None = None) -> None:
        """Called on the *old* actor instance just before it is replaced."""

    # -- Core message handling --

    async def receive(self, message: Any) -> None:
        raise NotImplementedError

    async def _run(self) -> None:
        self._running = True
        try:
            await self.pre_start()
        except Exception:
            logger.exception("Actor %s failed in pre_start", self.address)
            self._running = False
            return

        try:
            while self._running:
                try:
                    message = await self.mailbox.get()
                    try:
                        await self.receive(message)
                        self._message_count += 1
                    except Exception as exc:
                        logger.exception(
                            "Actor %s failed processing message (type=%s)",
                            self.address,
                            type(message).__name__,
                        )
                        await self._system._handle_actor_failure(self, exc, message)
                    finally:
                        self.mailbox.task_done()
                except asyncio.CancelledError:
                    break
        finally:
            try:
                await self.post_stop()
            except Exception:
                logger.exception("Actor %s failed in post_stop", self.address)

    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name=f"actor-{self.address}")

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def tell(self, message: Any) -> None:
        """Deliver a message to this actor's mailbox."""
        try:
            await self.mailbox.put(message)
        except MailboxFullError:
            logger.warning(
                "Mailbox full for actor %s — dropping message (type=%s)",
                self.address,
                type(message).__name__,
            )
            raise

    @property
    def uptime(self) -> float:
        """Seconds since this actor was created."""
        return time.monotonic() - self._created_at

    @property
    def message_count(self) -> int:
        return self._message_count
