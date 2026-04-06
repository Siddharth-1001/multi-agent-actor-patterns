# Architecture

This document explains the design of `multi-agent-actor-patterns`: the key abstractions, how they fit together, and the reasoning behind each decision.

---

## Design Philosophy

**Three constraints drive every decision:**

1. **No shared state.** Actors communicate only through messages. Nothing is mutated by more than one actor.
2. **Explicit failure.** Every error path is visible. Nothing fails silently.
3. **Inspectability over performance.** In agent orchestration, understanding what happened matters more than raw throughput.

---

## Core Abstractions

### Actor

The base unit of the system. An actor is an object that:

- Has a unique **address** (validated against `[a-zA-Z0-9._-]` pattern)
- Owns **private state** that only it can read or write
- Defines **behavior** — a handler function that processes one message at a time
- Processes messages **sequentially** from its bounded mailbox
- Supports **lifecycle hooks**: `pre_start()`, `post_stop()`, `pre_restart()`

```python
class Actor:
    address: ActorAddress
    mailbox: Mailbox          # bounded async queue
    state: dict               # private to this actor
    mailbox_capacity: int     # configurable per-subclass

    async def pre_start(self) -> None: ...    # setup hook
    async def receive(self, message) -> None: ...  # message handler
    async def post_stop(self) -> None: ...    # teardown hook
    async def pre_restart(self, reason) -> None: ...  # cleanup before restart
```

### Mailbox

Each actor has exactly one mailbox — a **bounded** async queue that buffers incoming messages. The actor's event loop drains the mailbox one message at a time, guaranteeing sequential processing.

Key properties:
- **Bounded capacity** (default: 10,000) — prevents memory exhaustion.
- Raises `MailboxFullError` when at capacity (backpressure signal).
- Tracks `total_enqueued` and `total_processed` for observability.
- `drain()` method for clean shutdown.

This is what makes actors thread-safe without locks: the mailbox is the only entry point to an actor's state.

### ActorSystem

The runtime that owns all actors. Responsibilities:

- **Registry**: maps addresses to actor instances
- **Scheduler**: drives each actor's message loop
- **Lifecycle manager**: spawns, stops, and shuts down actors
- **Dead letter routing**: catches messages to dead or overloaded actors
- **Graceful shutdown**: stops all actors in reverse order with a timeout

Supports async context manager: `async with ActorSystem() as system: ...`

```
ActorSystem
├── Registry { address → actor }
├── Scheduler (asyncio event loop)
└── DeadLetterActor
```

### SupervisorActor

A specialized actor that manages a set of child (worker) actors. The supervisor:

- Spawns worker actors
- Monitors them for failure signals
- Applies a **restart strategy** when a worker fails:
  - `RESTART`: kill and respawn the failed worker (with restart budget)
  - `STOP`: terminate the worker, don't replace it
  - `ESCALATE`: propagate the failure to this supervisor's own supervisor
- Enforces a **restart budget**: max N restarts within a time window. If exceeded, automatically escalates.

This forms a supervision tree — the same pattern Erlang OTP popularized.

```
RootSupervisor
└── ResearchSupervisor
    ├── WorkerActor(subtask_1)
    ├── WorkerActor(subtask_2)
    └── WorkerActor(subtask_3)
```

### DeadLetterActor

A system-level actor that receives any message that could not be delivered — because the destination actor crashed, was terminated, or never existed. Instead of silently dropping the message, `DeadLetterActor`:

- Logs the message, its intended recipient, and the failure reason
- Emits a `DEAD_LETTER` event that supervisors can observe
- Optionally retries delivery based on configured policy

This is the difference between a system that fails loudly (diagnosable) and one that fails silently (nightmare).

---

## Message Passing

All inter-actor communication uses typed `Message` objects — Python dataclasses validated by Pydantic.

```python
@dataclass
class ResearchRequest(Message):
    type: Literal["RESEARCH_REQUEST"]
    query: str
    depth: int
    reply_to: ActorAddress

@dataclass
class SubtaskResult(Message):
    type: Literal["SUBTASK_RESULT"]
    subtask_id: str
    content: str
    worker_address: ActorAddress
```

**Why typed messages:**
- Serializable — can be persisted, replayed, or transmitted over a network
- Self-documenting — the message type is the contract between actors
- Inspectable — every message in the system can be logged with full structure

---

## Research Agent Example: Message Flow

```
Client
  │
  │  RESEARCH_REQUEST { query, depth }
  ▼
ResearchSupervisor
  │  Decomposes query into N subtasks
  │
  ├──► WorkerActor(0)  SUBTASK { slice: "topic A" }
  ├──► WorkerActor(1)  SUBTASK { slice: "topic B" }
  └──► WorkerActor(2)  SUBTASK { slice: "topic C" }
            │
            │  SUBTASK_RESULT { content }
            ▼
      ResearchSupervisor
            │  Collects all results
            │  When all N results arrive → reconcile
            │
            │  RESEARCH_COMPLETE { summary }
            ▼
          Client
```

**Failure path:**

```
WorkerActor(1)  ← crashes mid-task
      │
      │  ACTOR_FAILED signal
      ▼
ResearchSupervisor
      │  Checks restart strategy
      │  Routes undelivered message → DeadLetterActor
      │  Spawns replacement WorkerActor(1')
      │  Resends SUBTASK
      ▼
WorkerActor(1')  ← retries the subtask
```

---

## Concurrency Model

The system uses `asyncio` as its scheduler. Each actor's message loop is a coroutine. Multiple actors run concurrently — but each individual actor processes one message at a time.

This gives us:
- **Concurrency** across actors (N workers run in parallel)
- **Sequential safety** within each actor (no locks needed)
- **Cooperative scheduling** (no preemption, predictable interleaving)

---

## What This Is Not

- **Not a distributed system.** All actors run in one process. Network transport (e.g., across machines) is on the roadmap but not implemented.
- **Not a framework for all agent patterns.** This focuses specifically on supervisor/worker hierarchies with message passing. It does not implement peer-to-peer agent graphs or consensus protocols.
- **Not production-hardened.** This is a reference implementation. Use it to understand patterns, validate designs, and build on top of — not as a drop-in production runtime.
