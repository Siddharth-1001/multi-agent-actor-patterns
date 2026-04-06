from __future__ import annotations

import logging
from typing import Any

from maap.core.actor import Actor
from maap.messages.types import DeadLetter

logger = logging.getLogger(__name__)


class DeadLetterActor(Actor):
    """Receives messages that could not be delivered to their intended recipient.

    Tracks a count of dead letters for observability. Override ``receive``
    to add custom alerting or persistence.
    """

    def __init__(self, address: str, system: Any) -> None:
        super().__init__(address, system)
        self.dead_letter_count: int = 0

    async def receive(self, message: Any) -> None:
        self.dead_letter_count += 1

        if isinstance(message, DeadLetter):
            logger.warning(
                "DEAD_LETTER #%d | recipient=%s | reason=%s | msg_type=%s",
                self.dead_letter_count,
                message.recipient,
                message.reason,
                type(message.original_message).__name__,
            )
        else:
            logger.warning(
                "DEAD_LETTER #%d | untyped message: %s",
                self.dead_letter_count,
                type(message).__name__,
            )
