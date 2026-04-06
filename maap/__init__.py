"""MAAP — Multi-Agent Actor Patterns.

A lightweight, async-first actor framework for building supervised
multi-agent systems in Python.
"""

from maap.core.actor import Actor, ActorAddress
from maap.core.errors import (
    ActorNotFoundError,
    InvalidAddressError,
    MaapError,
    MailboxFullError,
    RestartBudgetExhaustedError,
    SystemShutdownError,
)
from maap.core.supervisor import RestartStrategy, SupervisorActor
from maap.core.system import ActorSystem
from maap.messages.types import ActorFailed, DeadLetter, Message

__version__ = "0.2.0"

__all__ = [
    "Actor",
    "ActorAddress",
    "ActorFailed",
    "ActorNotFoundError",
    "ActorSystem",
    "DeadLetter",
    "InvalidAddressError",
    "MaapError",
    "MailboxFullError",
    "Message",
    "RestartBudgetExhaustedError",
    "RestartStrategy",
    "SupervisorActor",
    "SystemShutdownError",
]
