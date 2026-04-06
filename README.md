# MAAP — Multi-Agent Actor Patterns

[![CI](https://github.com/siddharthbhalsod/multi-agent-actor-patterns/actions/workflows/ci.yml/badge.svg)](https://github.com/siddharthbhalsod/multi-agent-actor-patterns/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)]()

A lightweight, async-first **Actor model** framework for building supervised multi-agent systems in Python. Designed for LLM-powered agent orchestration, research pipelines, and any workload that benefits from isolated, message-driven concurrency.

## Why MAAP?

In 2026, LLMs handle 95% of routine tasks — but the remaining 5% (coordination, failure recovery, backpressure) is where systems break. MAAP gives you **Erlang-style supervision** for Python agent systems:

| Problem | MAAP Solution |
|---|---|
| Shared mutable state between agents | Actors communicate only via **immutable messages** |
| One agent crash kills the system | **Supervisors** auto-restart or escalate failures |
| Unbounded work queues | **Bounded mailboxes** with configurable backpressure |
| Infinite restart loops | **Restart budgets** (max N restarts per time window) |
| No visibility into failures | **Dead letter** actor captures undelivered messages |
| Hard-to-test agent systems | Pure async Python — test with `pytest-asyncio` |

## Quick Start

### Installation

```bash
pip install maap
```

Or from source:

```bash
git clone https://github.com/siddharthbhalsod/multi-agent-actor-patterns.git
cd multi-agent-actor-patterns
pip install -e ".[dev]"
```

### Hello World — Define an Actor

```python
import asyncio
from maap import Actor, ActorSystem

class GreeterActor(Actor):
    async def receive(self, message):
        print(f"Hello, {message}!")

async def main():
    async with ActorSystem() as system:
        greeter = system.spawn(GreeterActor)
        await system.send(greeter.address, "World")
        await asyncio.sleep(0.1)

asyncio.run(main())
```

### Supervised Workers

```python
from maap import SupervisorActor, Actor, ActorSystem, RestartStrategy

class WorkerActor(Actor):
    async def receive(self, message):
        if message == "crash":
            raise RuntimeError("Something went wrong!")
        print(f"Worker processed: {message}")

class MySupervisor(SupervisorActor):
    restart_strategy = RestartStrategy.RESTART
    max_restarts = 3          # max 3 restarts...
    restart_window = 60.0     # ...within 60 seconds

    async def on_message(self, message):
        # Dispatch work to a child
        worker = self.spawn_worker(WorkerActor)
        await self._system.send(worker, message)

async def main():
    async with ActorSystem() as system:
        supervisor = system.spawn(MySupervisor)
        await system.send(supervisor.address, "do work")
        await system.send(supervisor.address, "crash")  # auto-restarted!

asyncio.run(main())
```

### Research Agent Example

A complete multi-agent pipeline that decomposes a research query, fans out to parallel workers, and aggregates results:

```bash
# With mock LLM (no API key needed):
python -m maap.examples.research_agent.main

# With a real LLM backend:
export ANTHROPIC_API_KEY=sk-ant-...
python -m maap.examples.research_agent.main
```

## Core Concepts

```
┌──────────────────────────────────────────┐
│               ActorSystem                │
│  ┌────────────────────────────────────┐  │
│  │         SupervisorActor            │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐      │  │
│  │  │Worker│ │Worker│ │Worker│      │  │
│  │  └──────┘ └──────┘ └──────┘      │  │
│  └────────────────────────────────────┘  │
│  ┌──────────────┐                        │
│  │ DeadLetterActor │ ← undelivered msgs  │
│  └──────────────┘                        │
└──────────────────────────────────────────┘
```

| Concept | Description |
|---|---|
| **Actor** | Isolated unit with a mailbox. Override `receive()` to handle messages. |
| **ActorSystem** | Creates, registers, and routes messages between actors. Supports graceful shutdown. |
| **SupervisorActor** | Manages child actors. Restarts, stops, or escalates on failure. |
| **Mailbox** | Bounded async queue. Rejects messages when full (backpressure). |
| **DeadLetterActor** | Captures messages sent to non-existent or full actors. |
| **Message** | Immutable Pydantic model. Type-safe, serializable, pattern-matchable. |

### Lifecycle Hooks

Actors support lifecycle hooks for setup and teardown:

```python
class MyActor(Actor):
    async def pre_start(self):
        """Called before the message loop begins."""
        self.db = await connect_db()

    async def post_stop(self):
        """Called after the message loop exits."""
        await self.db.close()

    async def pre_restart(self, reason=None):
        """Called on the OLD instance before replacement."""
        await self.cleanup()
```

### Restart Strategies

| Strategy | Behavior |
|---|---|
| `RESTART` | Respawn the failed child at the same address. Re-delivers the failed message. |
| `STOP` | Remove the failed child permanently. |
| `ESCALATE` | Stop the child and notify the supervisor's own supervisor. |

Restart budget: configurable `max_restarts` within a `restart_window` (seconds). If exhausted, the supervisor automatically escalates.

## Project Structure

```
maap/
├── __init__.py          # Public API exports
├── py.typed             # PEP 561 type marker
├── core/
│   ├── actor.py         # Actor base class, lifecycle hooks, address validation
│   ├── errors.py        # Custom exception hierarchy
│   ├── mailbox.py       # Bounded async mailbox
│   ├── supervisor.py    # Supervisor with restart budgets
│   ├── system.py        # ActorSystem with graceful shutdown
│   └── dead_letter.py   # Dead letter handler
├── messages/
│   └── types.py         # Pydantic message base classes
└── examples/
    └── research_agent/  # Complete working example
tests/                   # Full test suite (pytest-asyncio)
docs/                    # Architecture, changelog, contributing guide
```

## Development

```bash
# Setup
git clone https://github.com/siddharthbhalsod/multi-agent-actor-patterns.git
cd multi-agent-actor-patterns
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=maap --cov-report=term-missing

# Lint
ruff check .
ruff format --check .

# Type check
mypy maap/
```

## Security

Security is a first-class concern. See [SECURITY.md](SECURITY.md) for the full policy.

Key guardrails:
- **Bounded mailboxes** prevent memory exhaustion (DoS).
- **Address validation** rejects malformed or injected addresses.
- **Restart budgets** prevent infinite restart loops.
- **No secrets in logs** — error messages are truncated, API keys never logged.
- **Immutable messages** — no shared mutable state between actors.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for planned features including:
- Priority mailboxes and message TTL
- OpenTelemetry integration
- Request-reply (ask) pattern
- Web-based actor system visualizer
- Multi-process and network transport

## Contributing

Contributions are welcome! See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE).
