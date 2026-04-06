from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel


class Message(BaseModel):
    """Base class for all messages in the actor system."""

    model_config = {"frozen": True}


class ActorFailed(Message):
    type: Literal["ACTOR_FAILED"] = "ACTOR_FAILED"
    actor_address: str
    error: str
    failed_message: Any = None


class DeadLetter(Message):
    type: Literal["DEAD_LETTER"] = "DEAD_LETTER"
    recipient: str
    reason: str
    original_message: Any
