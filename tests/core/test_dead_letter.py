import asyncio
import logging

import pytest

from maap import ActorSystem


@pytest.mark.asyncio
async def test_sending_to_nonexistent_address_routes_to_dead_letter(caplog):
    system = ActorSystem()
    with caplog.at_level(logging.WARNING):
        await system.send("nonexistent-actor", {"payload": "hello"})
        await asyncio.sleep(0.1)
    assert "DEAD_LETTER" in caplog.text


@pytest.mark.asyncio
async def test_dead_letter_logs_message(caplog):
    system = ActorSystem()
    with caplog.at_level(logging.WARNING):
        await system.send("ghost-address", "spooky message")
        await asyncio.sleep(0.1)
    assert "ghost-address" in caplog.text
