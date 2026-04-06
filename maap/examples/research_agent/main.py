import asyncio
import logging
from typing import Any

from maap import ActorSystem
from maap.core.actor import Actor
from maap.examples.research_agent.messages import ResearchComplete, ResearchRequest
from maap.examples.research_agent.supervisor import ResearchSupervisor

logging.basicConfig(level=logging.INFO)


class ResultCollectorActor(Actor):
    async def receive(self, message: Any) -> None:
        match message:
            case ResearchComplete():
                await self._system.put_result(message)
            case _:
                pass


async def main() -> None:
    system = ActorSystem()
    supervisor = system.spawn(ResearchSupervisor)
    result_collector = system.spawn(ResultCollectorActor)

    await supervisor.tell(
        ResearchRequest(
            query="Summarize recent advances in multi-agent reinforcement learning",
            depth=3,
            reply_to=result_collector.address,
        ),
    )

    result: ResearchComplete = await system.await_result(timeout=30)
    print("\n=== Research Complete ===")
    print(f"Query: {result.query}")
    print(f"\nSummary:\n{result.summary}")


if __name__ == "__main__":
    asyncio.run(main())
