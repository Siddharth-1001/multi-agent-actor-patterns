import asyncio
from typing import Any

import pytest

from maap import Actor, ActorSystem
from maap.examples.research_agent.messages import (
    ResearchComplete,
    ResearchRequest,
)
from maap.examples.research_agent.supervisor import ResearchSupervisor


class ResultCollectorActor(Actor):
    async def receive(self, message: Any) -> None:
        match message:
            case ResearchComplete():
                await self._system.put_result(message)
            case _:
                pass


@pytest.mark.asyncio
async def test_full_research_pipeline():
    system = ActorSystem()
    supervisor = system.spawn(ResearchSupervisor)
    collector = system.spawn(ResultCollectorActor)

    await system.send(
        supervisor.address,
        ResearchRequest(
            query="test query",
            depth=2,
            reply_to=collector.address,
        ),
    )

    result = await system.await_result(timeout=10)
    assert isinstance(result, ResearchComplete)
    assert result.query == "test query"


@pytest.mark.asyncio
async def test_research_supervisor_decomposes_correctly():
    system = ActorSystem()
    sup: ResearchSupervisor = system.spawn(ResearchSupervisor)

    subtopics = sup._decompose_query("AI safety", 3)
    assert len(subtopics) == 3
    for t in subtopics:
        assert "AI safety" in t


@pytest.mark.asyncio
async def test_research_complete_has_correct_query():
    system = ActorSystem()
    supervisor = system.spawn(ResearchSupervisor)
    collector = system.spawn(ResultCollectorActor)

    query = "quantum computing applications"
    await system.send(
        supervisor.address,
        ResearchRequest(query=query, depth=2, reply_to=collector.address),
    )

    result = await system.await_result(timeout=10)
    assert result.query == query
    assert len(result.subtask_results) == 2


@pytest.mark.asyncio
async def test_worker_failure_and_restart():
    """Test that when a worker fails, supervisor respawns it."""
    from maap.core.actor import Actor

    system = ActorSystem()
    sup: ResearchSupervisor = system.spawn(ResearchSupervisor)

    # Manually spawn a worker that will fail
    class FailOnceWorker(Actor):
        _fail_count = 0

        async def receive(self, message: Any) -> None:
            if self.__class__._fail_count == 0:
                self.__class__._fail_count += 1
                raise RuntimeError("intentional failure")

    child_addr = sup.spawn_worker(FailOnceWorker)
    original_children_count = len(sup._children)

    await system.send(child_addr, "trigger-failure")
    await asyncio.sleep(0.2)

    # Children count should remain the same after restart
    assert len(sup._children) == original_children_count
