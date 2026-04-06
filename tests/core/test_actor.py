import asyncio

import pytest

from maap import Actor, ActorSystem


class EchoActor(Actor):
    def __init__(self, address, system):
        super().__init__(address, system)
        self.received: list = []

    async def receive(self, message) -> None:
        self.received.append(message)


class BombActor(Actor):
    async def receive(self, message) -> None:
        raise ValueError("Boom!")


@pytest.mark.asyncio
async def test_actor_receives_message():
    system = ActorSystem()
    actor = system.spawn(EchoActor)
    await system.send(actor.address, "hello")
    await asyncio.sleep(0.05)
    assert "hello" in actor.received


@pytest.mark.asyncio
async def test_actor_tell_puts_message_in_mailbox():
    system = ActorSystem()
    actor = system.spawn(EchoActor)
    await actor.tell("direct-tell")
    await asyncio.sleep(0.05)
    assert "direct-tell" in actor.received


@pytest.mark.asyncio
async def test_actor_failure_does_not_crash_system():
    system = ActorSystem()
    bomb = system.spawn(BombActor)
    await system.send(bomb.address, "trigger")
    await asyncio.sleep(0.1)
    # System is still alive — we can spawn new actors
    actor2 = system.spawn(EchoActor)
    await system.send(actor2.address, "still-alive")
    await asyncio.sleep(0.05)
    assert "still-alive" in actor2.received


@pytest.mark.asyncio
async def test_actor_stop():
    system = ActorSystem()
    actor = system.spawn(EchoActor)
    await actor.stop()
    assert not actor._running
