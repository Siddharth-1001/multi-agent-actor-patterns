import asyncio
import pytest
from maap import ActorSystem, Actor, SupervisorActor
from maap.core.supervisor import RestartStrategy
from maap.messages.types import ActorFailed


class FakeWorker(Actor):
    async def receive(self, message) -> None:
        pass


class BoomWorker(Actor):
    async def receive(self, message) -> None:
        raise RuntimeError("worker failed")


class RecordingSupervisor(SupervisorActor):
    restart_strategy = RestartStrategy.RESTART

    def __init__(self, address, system):
        super().__init__(address, system)
        self.failure_notices: list[ActorFailed] = []

    async def on_message(self, message) -> None:
        pass

    async def _handle_child_failure(self, failed_address, error, failed_message):
        self.failure_notices.append(
            ActorFailed(
                actor_address=failed_address, error=error, failed_message=failed_message
            )
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
    system = ActorSystem()
    sup: RecordingSupervisor = system.spawn(RecordingSupervisor)
    child_addr = sup.spawn_worker(BoomWorker)

    await system.send(child_addr, "crash-me")
    await asyncio.sleep(0.2)

    assert len(sup.failure_notices) >= 1
    # After RESTART, child_addr should still be in children (respawned)
    assert child_addr in sup._children


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
    system = ActorSystem()
    sup: RecordingSupervisor = system.spawn(RecordingSupervisor)
    child_addr = sup.spawn_worker(BoomWorker)

    await system.send(child_addr, "trigger")
    await asyncio.sleep(0.2)

    assert any(n.actor_address == child_addr for n in sup.failure_notices)
