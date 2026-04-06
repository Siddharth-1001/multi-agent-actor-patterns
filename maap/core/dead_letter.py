import logging
from typing import Any

from maap.core.actor import Actor

logger = logging.getLogger(__name__)


class DeadLetterActor(Actor):
    """Receives messages that could not be delivered to their intended recipient."""

    async def receive(self, message: Any) -> None:
        logger.warning(
            "DEAD_LETTER | recipient=%s | reason=%s | message=%s",
            message.recipient,
            message.reason,
            message.original_message,
        )
