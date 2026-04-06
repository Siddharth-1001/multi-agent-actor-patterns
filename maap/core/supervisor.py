from __future__ import annotations

import logging
import time
import uuid
from collections import deque
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
    """Supervisor that manages child actors with configurable failure handling.

    Class-level knobs (override in subclasses):
        restart_strategy : What to do when a child fails.
        max_restarts     : Max child restarts allowed within ``restart_window``.
        restart_window   : Rolling time window (seconds) for restart budget.
    """

    restart_strategy: RestartStrategy = RestartStrategy.RESTART
    max_restarts: int = 5
    restart_window: float = 60.0  # seconds

    def __init__(self, address: ActorAddress, system: Any) -> None:
        super().__init__(address, system)
        # child_address -> (actor_class, args, kwargs)
        _child_entry = tuple[type[Actor], tuple[Any, ...], dict[str, Any]]
        self._children: dict[ActorAddress, _child_entry] = {}
        # child_address -> deque of restart timestamps
        self._restart_history: dict[ActorAddress, deque[float]] = {}

    def spawn_worker(self, actor_class: type[Actor], *args: Any, **kwargs: Any) -> ActorAddress:
        child_address = f"{actor_class.__name__}-{uuid.uuid4().hex[:8]}"
        worker = self._system.spawn(
            actor_class,
            *args,
            supervisor=self.address,
            address=child_address,
            **kwargs,
        )
        self._children[worker.address] = (actor_class, args, kwargs)
        self._restart_history[worker.address] = deque()
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
        """Override to handle non-failure messages."""

    def _check_restart_budget(self, child_address: ActorAddress) -> bool:
        """Return True if another restart is allowed within the budget."""
        now = time.monotonic()
        history = self._restart_history.get(child_address, deque())
        # Evict entries outside the rolling window
        while history and (now - history[0]) > self.restart_window:
            history.popleft()
        return len(history) < self.max_restarts

    def _record_restart(self, child_address: ActorAddress) -> None:
        history = self._restart_history.setdefault(child_address, deque())
        history.append(time.monotonic())

    async def _handle_child_failure(
        self,
        failed_address: ActorAddress,
        error: str,
        failed_message: Any,
    ) -> None:
        strategy = self.restart_strategy
        logger.warning(
            "Supervisor %s handling failure of child %s with strategy %s | error=%s",
            self.address,
            failed_address,
            strategy.value,
            error[:200],
        )

        match strategy:
            case RestartStrategy.RESTART:
                if not self._check_restart_budget(failed_address):
                    logger.error(
                        "Restart budget exhausted for %s (%d in %ss) — escalating",
                        failed_address,
                        self.max_restarts,
                        self.restart_window,
                    )
                    # Escalate when budget is exhausted
                    self._children.pop(failed_address, None)
                    if self._supervisor_address:
                        await self._system.send(
                            self._supervisor_address,
                            ActorFailed(
                                actor_address=self.address,
                                error=(f"Restart budget exhausted for {failed_address}: {error}"),
                                failed_message=failed_message,
                            ),
                        )
                    return

                self._record_restart(failed_address)
                actor_class, args, kwargs = self._children[failed_address]

                # Stop old actor cleanly
                old_actor = self._system.get_actor(failed_address)
                if old_actor is not None:
                    try:
                        await old_actor.pre_restart(reason=None)
                    except Exception:
                        logger.exception("pre_restart failed for %s", failed_address)

                self._children.pop(failed_address, None)
                self._system._registry.pop(failed_address, None)

                new_worker = self._system.spawn(
                    actor_class,
                    *args,
                    supervisor=self.address,
                    address=failed_address,
                    **kwargs,
                )
                self._children[new_worker.address] = (actor_class, args, kwargs)

                # Re-deliver the failed message
                if failed_message is not None:
                    await self._system.send(new_worker.address, failed_message)

            case RestartStrategy.STOP:
                self._children.pop(failed_address, None)
                self._restart_history.pop(failed_address, None)
                await self._system.stop_actor(failed_address)

            case RestartStrategy.ESCALATE:
                self._children.pop(failed_address, None)
                self._restart_history.pop(failed_address, None)
                await self._system.stop_actor(failed_address)
                if self._supervisor_address:
                    await self._system.send(
                        self._supervisor_address,
                        ActorFailed(
                            actor_address=self.address,
                            error=f"Child {failed_address} failed: {error}",
                            failed_message=failed_message,
                        ),
                    )

    async def stop_all_children(self) -> None:
        """Gracefully stop all child actors."""
        for addr in list(self._children):
            await self._system.stop_actor(addr)
        self._children.clear()
        self._restart_history.clear()
