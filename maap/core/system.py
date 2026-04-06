from __future__ import annotations
import asyncio
import logging
import uuid
from typing import Any

from maap.core.actor import Actor, ActorAddress
from maap.messages.types import ActorFailed, DeadLetter

logger = logging.getLogger(__name__)

DEAD_LETTER_ADDRESS = "dead-letter"


class ActorSystem:
    def __init__(self) -> None:
        self._registry: dict[ActorAddress, Actor] = {}
        self._result_queue: asyncio.Queue[Any] = asyncio.Queue()
        # Import here to avoid circular imports
        from maap.core.dead_letter import DeadLetterActor

        self._dead_letter_actor = DeadLetterActor(DEAD_LETTER_ADDRESS, self)
        self._registry[DEAD_LETTER_ADDRESS] = self._dead_letter_actor
        self._dead_letter_actor.start()

    def spawn(
        self,
        actor_class: type[Actor],
        *args: Any,
        supervisor: ActorAddress | None = None,
        address: ActorAddress | None = None,
        **kwargs: Any,
    ) -> Actor:
        if address is None:
            address = f"{actor_class.__name__}-{uuid.uuid4().hex[:8]}"
        actor = actor_class(address, self, *args, **kwargs)
        actor._supervisor_address = supervisor
        self._registry[address] = actor
        actor.start()
        return actor

    async def send(self, address: ActorAddress, message: Any) -> None:
        actor = self._registry.get(address)
        if actor is None:
            dead_letter = DeadLetter(
                recipient=address,
                reason="Actor not found",
                original_message=message,
            )
            await self._dead_letter_actor.tell(dead_letter)
        else:
            await actor.tell(message)

    async def _handle_actor_failure(
        self, actor: Actor, error: Exception, message: Any
    ) -> None:
        failed_msg = ActorFailed(
            actor_address=actor.address,
            error=str(error),
            failed_message=message,
        )
        # Route failed message to dead letter
        dead_letter = DeadLetter(
            recipient=actor.address,
            reason=f"Actor raised exception: {error}",
            original_message=message,
        )
        await self._dead_letter_actor.tell(dead_letter)
        # Notify supervisor if any
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

    def terminate(self, address: ActorAddress) -> None:
        actor = self._registry.pop(address, None)
        if actor is not None:
            asyncio.create_task(actor.stop())
