"""Tests for bounded mailbox, lifecycle hooks, graceful shutdown, and address validation."""

import asyncio
from typing import Any

import pytest

from maap import Actor, ActorSystem
from maap.core.errors import InvalidAddressError, MailboxFullError, SystemShutdownError
from maap.core.mailbox import Mailbox

# --- Mailbox tests ---


class _SmallMailboxActor(Actor):
    mailbox_capacity = 3

    async def receive(self, message: Any) -> None:
        # Simulate slow processing
        await asyncio.sleep(0.5)


@pytest.mark.asyncio
async def test_bounded_mailbox_rejects_when_full():
    mb = Mailbox(capacity=2, owner_address="test-actor")
    await mb.put("a")
    await mb.put("b")
    with pytest.raises(MailboxFullError):
        await mb.put("c")


@pytest.mark.asyncio
async def test_mailbox_drain():
    mb = Mailbox(capacity=10, owner_address="test-drain")
    await mb.put("x")
    await mb.put("y")
    drained = await mb.drain()
    assert drained == ["x", "y"]
    assert mb.depth == 0


@pytest.mark.asyncio
async def test_mailbox_counters():
    mb = Mailbox(capacity=10, owner_address="test-counters")
    await mb.put("a")
    await mb.put("b")
    assert mb.total_enqueued == 2
    await mb.get()
    assert mb.total_processed == 1


# --- Lifecycle hook tests ---


class _LifecycleActor(Actor):
    def __init__(self, address, system):
        super().__init__(address, system)
        self.hooks_called: list[str] = []

    async def pre_start(self) -> None:
        self.hooks_called.append("pre_start")

    async def post_stop(self) -> None:
        self.hooks_called.append("post_stop")

    async def receive(self, message: Any) -> None:
        self.hooks_called.append(f"receive:{message}")


@pytest.mark.asyncio
async def test_lifecycle_hooks_called():
    system = ActorSystem()
    actor: _LifecycleActor = system.spawn(_LifecycleActor)
    await asyncio.sleep(0.05)
    await system.send(actor.address, "hello")
    await asyncio.sleep(0.05)
    await actor.stop()
    assert "pre_start" in actor.hooks_called
    assert "receive:hello" in actor.hooks_called
    assert "post_stop" in actor.hooks_called


# --- Address validation tests ---


def test_valid_addresses():
    from maap.core.actor import validate_address

    validate_address("MyActor-abc123")
    validate_address("actor.worker.1")
    validate_address("a")


def test_invalid_addresses():
    from maap.core.actor import validate_address

    with pytest.raises(InvalidAddressError):
        validate_address("")
    with pytest.raises(InvalidAddressError):
        validate_address("-starts-with-dash")
    with pytest.raises(InvalidAddressError):
        validate_address("has spaces")
    with pytest.raises(InvalidAddressError):
        validate_address("has/slash")


# --- Graceful shutdown tests ---


@pytest.mark.asyncio
async def test_actor_system_shutdown():
    system = ActorSystem()
    system.spawn(_LifecycleActor)
    assert system.actor_count >= 2  # actor + dead-letter
    await system.shutdown()
    assert system.actor_count == 0
    assert not system.is_running


@pytest.mark.asyncio
async def test_actor_system_context_manager():
    async with ActorSystem() as system:
        system.spawn(_LifecycleActor)
        assert system.is_running
    assert not system.is_running


@pytest.mark.asyncio
async def test_spawn_after_shutdown_raises():
    system = ActorSystem()
    await system.shutdown()
    with pytest.raises(SystemShutdownError):
        system.spawn(_LifecycleActor)


# --- Actor property tests ---


@pytest.mark.asyncio
async def test_actor_uptime():
    system = ActorSystem()
    actor = system.spawn(_LifecycleActor)
    await asyncio.sleep(0.05)
    assert actor.uptime > 0


@pytest.mark.asyncio
async def test_actor_message_count():
    system = ActorSystem()
    actor: _LifecycleActor = system.spawn(_LifecycleActor)
    await system.send(actor.address, "a")
    await system.send(actor.address, "b")
    await asyncio.sleep(0.1)
    assert actor.message_count == 2
