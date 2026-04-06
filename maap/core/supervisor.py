from __future__ import annotations
import logging
import uuid
from enum import Enum
from typing import Any

from maap.core.actor import Actor, ActorAddress
from maap.messages.types import ActorFailed

logger = logging.getLogger(__name__)


class RestartStrategy(Enum):
    RESTART = "RESTART"
    STOP = "STOP"
    ESCALATE = "ESCALATE"


class SupervisorActor(Actor):
    restart_strategy: RestartStrategy = RestartStrategy.RESTART

    def __init__(self, address: ActorAddress, system: Any) -> None:
        super().__init__(address, system)
        # maps child_address -> (actor_class, args, kwargs)
        self._children: dict[ActorAddress, tuple[type[Actor], tuple, dict]] = {}

    def spawn_worker(
        self, actor_class: type[Actor], *args: Any, **kwargs: Any
    ) -> ActorAddress:
        child_address = f"{actor_class.__name__}-{uuid.uuid4().hex[:8]}"
        worker = self._system.spawn(
            actor_class,
            *args,
            supervisor=self.address,
            address=child_address,
            **kwargs,
        )
        self._children[worker.address] = (actor_class, args, kwargs)
        return worker.address

    async def receive(self, message: Any) -> None:
        match message:
            case ActorFailed() if message.actor_address in self._children:
                await self._handle_child_failure(
                    message.actor_address, message.error, message.failed_message
                )
            case _:
                await self.on_message(message)

    async def on_message(self, message: Any) -> None:
        pass

    async def _handle_child_failure(
        self,
        failed_address: ActorAddress,
        error: str,
        failed_message: Any,
    ) -> None:
        strategy = self.restart_strategy
        logger.warning(
            "Supervisor %s handling failure of child %s with strategy %s. Error: %s",
            self.address,
            failed_address,
            strategy,
            error,
        )
        match strategy:
            case RestartStrategy.RESTART:
                actor_class, args, kwargs = self._children[failed_address]
                # Remove old entry
                self._children.pop(failed_address, None)
                self._system._registry.pop(failed_address, None)
                # Respawn at the same address
                new_worker = self._system.spawn(
                    actor_class,
                    *args,
                    supervisor=self.address,
                    address=failed_address,
                    **kwargs,
                )
                self._children[new_worker.address] = (actor_class, args, kwargs)
                # Resend the failed message if available
                if failed_message is not None:
                    await self._system.send(new_worker.address, failed_message)
            case RestartStrategy.STOP:
                self._children.pop(failed_address, None)
                self._system.terminate(failed_address)
            case RestartStrategy.ESCALATE:
                self._children.pop(failed_address, None)
                if self._supervisor_address:
                    await self._system.send(
                        self._supervisor_address,
                        ActorFailed(
                            actor_address=self.address,
                            error=f"Child {failed_address} failed: {error}",
                            failed_message=failed_message,
                        ),
                    )
