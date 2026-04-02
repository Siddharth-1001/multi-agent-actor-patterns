# multi-agent-actor-patterns

> A clean reference implementation of the Actor model applied to multi-agent AI systems.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)]()

---

## What Is This?

`multi-agent-actor-patterns` is a reference framework that applies the **Actor model** — a well-proven concurrency pattern from distributed systems — to orchestrating multi-agent AI pipelines.

Instead of shared state, global variables, or tangled callbacks, agents here communicate **only through messages**. Each agent is isolated, owns its state, and interacts with the world exclusively by sending and receiving typed messages.

This is the architecture that makes multi-agent systems **debuggable, fault-tolerant, and scalable**.

---

## Why the Actor Model for Agents?

Most multi-agent frameworks bolt agents together with direct function calls or shared memory. This works until it doesn't — race conditions, unclear ownership, and cascading failures with no recovery path.

The Actor model solves this structurally:

| Problem | Actor Model Solution |
|---|---|
| Shared state bugs | Each actor owns its own state exclusively |
| Cascading failures | Supervisor trees isolate and recover failures |
| Hard to debug | Every message is logged; full audit trail |
| Tight coupling | Actors communicate only via typed messages |

---

## Core Concepts

### Actor
The fundamental unit. An actor has:
- A unique address (mailbox)
- Private state it alone can mutate
- Behavior defined by how it handles incoming messages

### Supervisor → Worker Hierarchy
Supervisors manage a pool of worker actors. When a worker fails, the supervisor decides: restart it, stop it, or escalate. Workers never know about each other.

```
SupervisorActor
├── WorkerActor(task_1)
├── WorkerActor(task_2)
└── WorkerActor(task_3)
```

### Message Passing
All communication is asynchronous and explicit. No shared memory. Messages are typed dataclasses — serializable, inspectable, and replayable.

### Dead Letter Handling
Messages sent to failed or non-existent actors are routed to a `DeadLetterActor` instead of being silently dropped. You always know what was lost and why.

---

## Quickstart

```bash
pip install multi-agent-actor-patterns
```

### Run the Research Agent Example

```python
from maap import ActorSystem, ResearchSupervisor

# Boot the actor system
system = ActorSystem()

# Spawn the research supervisor
supervisor = system.spawn(ResearchSupervisor)

# Send a research task — it breaks this into sub-agents automatically
supervisor.tell({
    "type": "RESEARCH_REQUEST",
    "query": "Summarize recent advances in multi-agent reinforcement learning",
    "depth": 3  # number of sub-agent workers to spawn
})

# Collect results
result = system.await_result(timeout=60)
print(result.summary)
```

---

## Working Example: Research Agent

The flagship example demonstrates a full supervisor/worker pipeline:

1. `ResearchSupervisor` receives a high-level query
2. It decomposes the query into N sub-topics
3. It spawns one `ResearchWorkerActor` per sub-topic
4. Each worker independently researches its slice
5. The supervisor reconciles all worker results into a final summary
6. If any worker fails, the dead letter handler captures its message and the supervisor retries or skips

```
ResearchSupervisor
│  Receives: RESEARCH_REQUEST
│  Sends:    SUBTASK to each worker
│
├── ResearchWorkerActor("reinforcement learning basics")
├── ResearchWorkerActor("multi-agent coordination")
├── ResearchWorkerActor("recent benchmarks")
│
└── On completion: RECONCILE_RESULTS → final summary
```

---

## Project Structure

```
multi-agent-actor-patterns/
├── maap/
│   ├── core/
│   │   ├── actor.py          # Base Actor class
│   │   ├── system.py         # ActorSystem (registry + scheduler)
│   │   ├── mailbox.py        # Async message queue
│   │   ├── supervisor.py     # SupervisorActor base class
│   │   └── dead_letter.py    # DeadLetterActor
│   ├── messages/
│   │   └── types.py          # Typed message definitions
│   └── examples/
│       └── research_agent/   # Full research pipeline example
├── tests/
├── docs/
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── ROADMAP.md
└── CHANGELOG.md
```

---

## Requirements

- Python 3.10+
- `asyncio` (stdlib)
- `pydantic` >= 2.0 (message validation)

Optional for the research example:
- Anthropic API key (set as `ANTHROPIC_API_KEY`)

---

## Documentation

| Document | Description |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Design decisions, message flow diagrams, pattern explanations |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute code, open issues, and submit PRs |
| [ROADMAP.md](ROADMAP.md) | Planned features and milestones |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

---

## Status

This project is in **alpha**. The core actor primitives and research example are stable. APIs may shift before v1.0. See [ROADMAP.md](ROADMAP.md) for what's next.

---

## License

MIT — see [LICENSE](LICENSE).
