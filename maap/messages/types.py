from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    """Base class for all messages in the actor system.

    Messages are immutable (frozen) Pydantic models.  Every message
    carries a ``type`` discriminator to enable safe pattern matching.
    """

    model_config = {"frozen": True}


class ActorFailed(Message):
    """Notification that an actor failed while processing a message."""

    type: Literal["ACTOR_FAILED"] = "ACTOR_FAILED"
    actor_address: str = Field(..., max_length=255)
    error: str = Field(..., max_length=4096)
    failed_message: Any = None

    @field_validator("error", mode="before")
    @classmethod
    def _truncate_error(cls, v: Any) -> str:
        s = str(v)
        return s[:4096] if len(s) > 4096 else s


class DeadLetter(Message):
    """Envelope for messages that could not be delivered."""

    type: Literal["DEAD_LETTER"] = "DEAD_LETTER"
    recipient: str = Field(..., max_length=255)
    reason: str = Field(..., max_length=4096)
    original_message: Any = None
