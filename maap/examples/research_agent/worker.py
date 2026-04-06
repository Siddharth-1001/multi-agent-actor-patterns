from __future__ import annotations
import logging
import os
from typing import Any

from maap.core.actor import Actor
from maap.examples.research_agent.messages import SubTask, SubTaskResult

logger = logging.getLogger(__name__)


class ResearchWorkerActor(Actor):
    async def receive(self, message: Any) -> None:
        match message:
            case SubTask():
                result = await self._do_research(message)
                await self._system.send(message.reply_to, result)
            case _:
                logger.warning(
                    "ResearchWorkerActor %s received unexpected message: %r",
                    self.address,
                    message,
                )

    async def _do_research(self, task: SubTask) -> SubTaskResult:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            content = await self._call_anthropic(task.query_slice, api_key)
        else:
            content = self._mock_research(task.query_slice)
        return SubTaskResult(
            subtask_id=task.subtask_id,
            content=content,
            worker_address=self.address,
        )

    def _mock_research(self, query_slice: str) -> str:
        return (
            f"Research findings for '{query_slice}':\n"
            f"- Key insight 1 about {query_slice}\n"
            f"- Key insight 2 about {query_slice}\n"
            f"- Summary: This subtopic covers important aspects of {query_slice}."
        )

    async def _call_anthropic(self, query_slice: str, api_key: str) -> str:
        try:
            import anthropic  # type: ignore[import-not-found]

            client = anthropic.AsyncAnthropic(api_key=api_key)
            response = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=512,
                messages=[
                    {
                        "role": "user",
                        "content": f"Research the following topic briefly: {query_slice}",
                    }
                ],
            )
            return response.content[0].text
        except Exception as exc:
            logger.warning("Anthropic call failed, falling back to mock: %s", exc)
            return self._mock_research(query_slice)
