"""Custom exceptions for the MAAP actor system."""

from __future__ import annotations


class MaapError(Exception):
    """Base exception for all MAAP errors."""


class ActorNotFoundError(MaapError):
    """Raised when an actor cannot be found in the registry."""

    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__(f"Actor not found: {address}")


class MailboxFullError(MaapError):
    """Raised when an actor's mailbox has reached capacity."""

    def __init__(self, address: str, capacity: int) -> None:
        self.address = address
        self.capacity = capacity
        super().__init__(f"Mailbox full for actor {address} (capacity={capacity})")


class ActorStartupError(MaapError):
    """Raised when an actor fails during startup."""


class RestartBudgetExhaustedError(MaapError):
    """Raised when a supervisor exceeds its restart budget."""

    def __init__(self, address: str, max_restarts: int, window_seconds: float) -> None:
        self.address = address
        super().__init__(
            f"Restart budget exhausted for {address}: {max_restarts} restarts in {window_seconds}s"
        )


class SystemShutdownError(MaapError):
    """Raised when operations are attempted on a shut-down system."""


class MessageValidationError(MaapError):
    """Raised when a message fails validation."""


class InvalidAddressError(MaapError):
    """Raised when an actor address is invalid."""

    def __init__(self, address: str, reason: str) -> None:
        self.address = address
        super().__init__(f"Invalid actor address '{address}': {reason}")
