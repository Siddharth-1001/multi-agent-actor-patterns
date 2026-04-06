from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from maap.core.actor import Actor, ActorAddress, validate_address
from maap.core.errors import MailboxFullError, SystemShutdownError
from maap.messages.types import ActorFailed, DeadLetter

logger = logging.getLogger(__name__)

DEAD_LETTER_ADDRESS = "dead-letter"


class ActorSystem:
    """Central registry and message router for all actors.

    Supports graceful shutdown via ``shutdown()`` and can be used as an
    async context manager::

        async with ActorSystem() as system:
            actor = system.spawn(MyActor)
            ...
    """

    def __init__(self) -> None:
        self._registry: dict[ActorAddress, Actor] = {}
        self._result_queue: asyncio.Queue[Any] = asyncio.Queue()
        self._shutting_down: bool = False
        self._background_tasks: set[asyncio.Task[None]] = set()

        from maap.core.dead_letter import DeadLetterActor

        self._dead_letter_actor = DeadLetterActor(DEAD_LETTER_ADDRESS, self)
        self._registry[DEAD_LETTER_ADDRESS] = self._dead_letter_actor
        self._dead_letter_actor.start()

    # -- Async context manager --

    async def __aenter__(self) -> ActorSystem:
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.shutdown()

    # -- Actor lifecycle --

    def spawn(
        self,
        actor_class: type[Actor],
        *args: Any,
        supervisor: ActorAddress | None = None,
        address: ActorAddress | None = None,
        **kwargs: Any,
    ) -> Actor:
        if self._shutting_down:
            raise SystemShutdownError("Cannot spawn actors during shutdown")

        if address is None:
            # Strip leading underscores from class names (e.g. test helpers).
            safe_name = actor_class.__name__.lstrip("_") or "Actor"
            address = f"{safe_name}-{uuid.uuid4().hex[:8]}"
        else:
            validate_address(address)

        if address in self._registry:
            logger.warning("Replacing existing actor at address %s", address)
            old_actor = self._registry.pop(address)
            task = asyncio.create_task(old_actor.stop())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        actor = actor_class(address, self, *args, **kwargs)
        actor._supervisor_address = supervisor
        self._registry[address] = actor
        actor.start()
        return actor

    async def send(self, address: ActorAddress, message: Any) -> None:
        """Route *message* to the actor at *address*.

        If the actor is not found, the message is forwarded to the dead
        letter actor.
        """
        if self._shutting_down:
            logger.debug(
                "Message dropped during shutdown: %s -> %s",
                address,
                type(message).__name__,
            )
            return

        actor = self._registry.get(address)
        if actor is None:
            dead_letter = DeadLetter(
                recipient=address,
                reason="Actor not found",
                original_message=message,
            )
            await self._dead_letter_actor.tell(dead_letter)
        else:
            try:
                await actor.tell(message)
            except MailboxFullError:
                dead_letter = DeadLetter(
                    recipient=address,
                    reason="Mailbox full",
                    original_message=message,
                )
                await self._dead_letter_actor.tell(dead_letter)

    async def _handle_actor_failure(self, actor: Actor, error: Exception, message: Any) -> None:
        error_str = str(error)[:4096]
        failed_msg = ActorFailed(
            actor_address=actor.address,
            error=error_str,
            failed_message=message,
        )
        dead_letter = DeadLetter(
            recipient=actor.address,
            reason=f"Actor raised exception: {type(error).__name__}",
            original_message=message,
        )
        await self._dead_letter_actor.tell(dead_letter)

        if actor._supervisor_address:
            sup_actor = self._registry.get(actor._supervisor_address)
            if sup_actor:
                await sup_actor.tell(failed_msg)

    async def put_result(self, result: Any) -> None:
        await self._result_queue.put(result)

    async def await_result(self, timeout: float = 60.0) -> Any:
        return await asyncio.wait_for(self._result_queue.get(), timeout=timeout)

    def get_actor(self, address: ActorAddress) -> Actor | None:
        return self._registry.get(address)

    async def stop_actor(self, address: ActorAddress) -> None:
        """Gracefully stop an actor and remove it from the registry."""
        actor = self._registry.pop(address, None)
        if actor is not None:
            await actor.stop()

    def terminate(self, address: ActorAddress) -> None:
        """Fire-and-forget stop (backward compat). Prefer ``stop_actor``."""
        actor = self._registry.pop(address, None)
        if actor is not None:
            task = asyncio.create_task(actor.stop())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    async def shutdown(self, timeout: float = 10.0) -> None:
        """Gracefully shut down the entire actor system.

        Stops all actors in reverse-registration order and waits up to
        *timeout* seconds for them to finish.
        """
        if self._shutting_down:
            return
        self._shutting_down = True
        logger.info("ActorSystem shutting down (%d actors)", len(self._registry))

        addresses = list(reversed(self._registry.keys()))
        stop_tasks = []
        for addr in addresses:
            a = self._registry.pop(addr, None)
            if a is not None:
                stop_tasks.append(asyncio.create_task(a.stop()))

        if stop_tasks:
            _done, pending = await asyncio.wait(stop_tasks, timeout=timeout)
            for task in pending:
                task.cancel()

        self._registry.clear()
        logger.info("ActorSystem shutdown complete")

    @property
    def actor_count(self) -> int:
        return len(self._registry)

    @property
    def is_running(self) -> bool:
        return not self._shutting_down
