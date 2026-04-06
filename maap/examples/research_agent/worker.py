from __future__ import annotations

import logging
import os
from typing import Any

from maap.core.actor import Actor
from maap.examples.research_agent.messages import SubTask, SubTaskResult

logger = logging.getLogger(__name__)

# Configurable via environment; defaults to a current, cost-effective model.
DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_QUERY_LENGTH = 2000


class ResearchWorkerActor(Actor):
    async def receive(self, message: Any) -> None:
        match message:
            case SubTask():
                result = await self._do_research(message)
                await self._system.send(message.reply_to, result)
            case _:
                logger.warning(
                    "ResearchWorkerActor %s received unexpected message type=%s",
                    self.address,
                    type(message).__name__,
                )

    async def _do_research(self, task: SubTask) -> SubTaskResult:
        # Sanitize query length to prevent abuse
        query = task.query_slice[:MAX_QUERY_LENGTH]

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            content = await self._call_anthropic(query, api_key)
        else:
            content = self._mock_research(query)
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
            import anthropic

            model = os.environ.get("MAAP_LLM_MODEL", DEFAULT_MODEL)
            client = anthropic.AsyncAnthropic(api_key=api_key)
            response = await client.messages.create(
                model=model,
                max_tokens=512,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Research the following topic briefly and factually. "
                            f"Topic: {query_slice}"
                        ),
                    }
                ],
            )
            result: str = response.content[0].text
            return result
        except Exception as exc:
            # Never log the API key — only log the exception type and message
            logger.warning(
                "LLM call failed (%s), falling back to mock",
                type(exc).__name__,
            )
            return self._mock_research(query_slice)
