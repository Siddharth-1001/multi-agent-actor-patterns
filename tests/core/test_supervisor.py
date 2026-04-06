import asyncio
from typing import ClassVar

import pytest

from maap import Actor, ActorSystem, SupervisorActor
from maap.core.supervisor import RestartStrategy
from maap.messages.types import ActorFailed


class FakeWorker(Actor):
    async def receive(self, message) -> None:
        pass


class BoomWorker(Actor):
    async def receive(self, message) -> None:
        raise RuntimeError("worker failed")


class FailOnceWorker(Actor):
    """Fails on the first message, succeeds on subsequent ones."""

    _fail_flags: ClassVar[dict[str, bool]] = {}

    async def receive(self, message) -> None:
        if not self.__class__._fail_flags.get(self.address, False):
            self.__class__._fail_flags[self.address] = True
            raise RuntimeError("first-time failure")


class RecordingSupervisor(SupervisorActor):
    restart_strategy = RestartStrategy.RESTART

    def __init__(self, address, system):
        super().__init__(address, system)
        self.failure_notices: list[ActorFailed] = []

    async def on_message(self, message) -> None:
        pass

    async def _handle_child_failure(self, failed_address, error, failed_message):
        self.failure_notices.append(
            ActorFailed(actor_address=failed_address, error=error, failed_message=failed_message)
        )
        await super()._handle_child_failure(failed_address, error, failed_message)


class StopStrategySupervisor(SupervisorActor):
    restart_strategy = RestartStrategy.STOP

    async def on_message(self, message) -> None:
        pass


@pytest.mark.asyncio
async def test_spawn_workers_under_supervisor():
    system = ActorSystem()
    sup: RecordingSupervisor = system.spawn(RecordingSupervisor)
    child_addr = sup.spawn_worker(FakeWorker)
    assert child_addr in sup._children
    assert system.get_actor(child_addr) is not None


@pytest.mark.asyncio
async def test_restart_strategy_respawns_worker():
    """Restart strategy re-spawns a worker that recovers on retry."""
    FailOnceWorker._fail_flags.clear()
    system = ActorSystem()
    sup: RecordingSupervisor = system.spawn(RecordingSupervisor)
    child_addr = sup.spawn_worker(FailOnceWorker)

    await system.send(child_addr, "crash-me")
    await asyncio.sleep(0.3)

    assert len(sup.failure_notices) >= 1
    # After RESTART, child_addr should still be in children (respawned)
    assert child_addr in sup._children


@pytest.mark.asyncio
async def test_restart_budget_exhaustion():
    """A perpetually-failing worker exhausts the restart budget."""
    system = ActorSystem()
    sup: RecordingSupervisor = system.spawn(RecordingSupervisor)
    child_addr = sup.spawn_worker(BoomWorker)

    await system.send(child_addr, "crash-me")
    await asyncio.sleep(1.0)

    # Budget of 5 restarts should have been exhausted
    assert len(sup.failure_notices) >= sup.max_restarts
    # Child removed after budget exhaustion
    assert child_addr not in sup._children


@pytest.mark.asyncio
async def test_stop_strategy_removes_worker():
    system = ActorSystem()
    sup: StopStrategySupervisor = system.spawn(StopStrategySupervisor)
    child_addr = sup.spawn_worker(BoomWorker)

    await system.send(child_addr, "crash-me")
    await asyncio.sleep(0.2)

    assert child_addr not in sup._children


@pytest.mark.asyncio
async def test_supervisor_receives_actor_failed():
    FailOnceWorker._fail_flags.clear()
    system = ActorSystem()
    sup: RecordingSupervisor = system.spawn(RecordingSupervisor)
    child_addr = sup.spawn_worker(FailOnceWorker)

    await system.send(child_addr, "trigger")
    await asyncio.sleep(0.3)

    assert any(n.actor_address == child_addr for n in sup.failure_notices)
