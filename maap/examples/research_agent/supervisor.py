from __future__ import annotations

import logging
import uuid
from typing import Any

from maap.core.supervisor import RestartStrategy, SupervisorActor
from maap.examples.research_agent.messages import (
    ResearchComplete,
    ResearchRequest,
    SubTask,
    SubTaskResult,
)
from maap.examples.research_agent.worker import ResearchWorkerActor

logger = logging.getLogger(__name__)


class ResearchSupervisor(SupervisorActor):
    restart_strategy = RestartStrategy.RESTART

    def __init__(self, address: str, system: Any) -> None:
        super().__init__(address, system)
        self._pending: dict[str, SubTask] = {}  # subtask_id -> SubTask
        self._results: dict[str, SubTaskResult] = {}  # subtask_id -> result
        self._reply_to: str | None = None
        self._current_query: str | None = None

    def _decompose_query(self, query: str, depth: int) -> list[str]:
        subtopics = [
            f"{query} — foundations and background",
            f"{query} — recent developments and state of the art",
            f"{query} — practical applications and case studies",
            f"{query} — challenges and open problems",
            f"{query} — future directions",
        ]
        return subtopics[:depth]

    async def on_message(self, message: Any) -> None:
        match message:
            case ResearchRequest():
                await self._handle_research_request(message)
            case SubTaskResult():
                await self._handle_subtask_result(message)
            case _:
                logger.warning("ResearchSupervisor received unexpected message: %r", message)

    async def _handle_research_request(self, request: ResearchRequest) -> None:
        self._reply_to = request.reply_to
        self._current_query = request.query
        self._pending.clear()
        self._results.clear()

        subtopics = self._decompose_query(request.query, request.depth)
        for subtopic in subtopics:
            subtask_id = uuid.uuid4().hex[:8]
            subtask = SubTask(
                subtask_id=subtask_id,
                query_slice=subtopic,
                reply_to=self.address,
            )
            self._pending[subtask_id] = subtask
            worker_addr = self.spawn_worker(ResearchWorkerActor)
            await self._system.send(worker_addr, subtask)

    async def _handle_subtask_result(self, result: SubTaskResult) -> None:
        self._results[result.subtask_id] = result
        self._pending.pop(result.subtask_id, None)

        if not self._pending and self._reply_to and self._current_query:
            summary_parts = []
            ordered = sorted(self._results.values(), key=lambda r: r.subtask_id)
            for r in ordered:
                summary_parts.append(r.content)
            summary = "\n\n".join(summary_parts)

            complete = ResearchComplete(
                query=self._current_query,
                summary=summary,
                subtask_results=list(ordered),
            )
            await self._system.send(self._reply_to, complete)

    async def _handle_child_failure(
        self,
        failed_address: str,
        error: str,
        failed_message: Any,
    ) -> None:
        # Call parent to respawn the worker
        await super()._handle_child_failure(failed_address, error, failed_message)
