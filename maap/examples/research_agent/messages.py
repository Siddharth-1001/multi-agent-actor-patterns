from __future__ import annotations

from typing import Literal

from maap.messages.types import Message


class ResearchRequest(Message):
    type: Literal["RESEARCH_REQUEST"] = "RESEARCH_REQUEST"
    query: str
    depth: int = 3
    reply_to: str  # ActorAddress to send RESEARCH_COMPLETE to


class SubTask(Message):
    type: Literal["SUBTASK"] = "SUBTASK"
    subtask_id: str
    query_slice: str
    reply_to: str  # supervisor address


class SubTaskResult(Message):
    type: Literal["SUBTASK_RESULT"] = "SUBTASK_RESULT"
    subtask_id: str
    content: str
    worker_address: str


class ResearchComplete(Message):
    type: Literal["RESEARCH_COMPLETE"] = "RESEARCH_COMPLETE"
    query: str
    summary: str
    subtask_results: list[SubTaskResult]
