# Roadmap

This document tracks what's built, what's in progress, and where the project is heading.

Status key: ✅ Done · 🔨 In Progress · 📋 Planned · 💡 Idea

---

## v0.1 — Foundation (Current)

The goal of v0.1 is to establish the core actor primitives and ship one working end-to-end example.

| Feature | Status |
|---|---|
| Base `Actor` class with async mailbox | ✅ |
| `ActorSystem` registry and scheduler | ✅ |
| `SupervisorActor` with RESTART strategy | ✅ |
| Typed `Message` base class (Pydantic) | ✅ |
| `DeadLetterActor` with logging | ✅ |
| Research Agent example (supervisor → workers → reconcile) | ✅ |
| README and ARCHITECTURE documentation | ✅ |

---

## v0.2 — Supervision Maturity

Expand the supervisor model to cover the full range of real-world failure scenarios.

| Feature | Status |
|---|---|
| STOP and ESCALATE restart strategies | 📋 |
| Supervisor restart budget (max restarts / time window) | 📋 |
| Worker timeout detection | 📋 |
| Backoff on worker restart | 📋 |
| Dead letter retry policy (configurable) | 📋 |
| Structured failure events observable by parent supervisor | 📋 |

---

## v0.3 — Message Infrastructure

Make the message layer more powerful for production-adjacent use cases.

| Feature | Status |
|---|---|
| Message priority queue (high / normal / low) | 📋 |
| Message TTL (time-to-live, auto-dead-letter on expiry) | 📋 |
| Request/reply pattern with futures (`ask` pattern) | 📋 |
| Message tracing with correlation IDs | 📋 |
| Full message audit log (persist to disk) | 📋 |
| Message replay from audit log | 📋 |

---

## v0.4 — More Examples

Demonstrate additional multi-agent topologies beyond supervisor/worker.

| Example | Status | Description |
|---|---|---|
| Pipeline Agent | 📋 | Linear chain: Agent A → B → C → D |
| Fan-out / Fan-in | 📋 | One supervisor, N parallel workers, merge results |
| Retry with circuit breaker | 📋 | Worker that fails intermittently; supervisor with breaker |
| Stateful conversation agent | 📋 | Actor that accumulates context across multiple messages |
| Tool-use agent | 📋 | Worker actor that calls external tools as part of its task |

---

## v0.5 — Observability

Make it easy to understand what the system is doing in real time.

| Feature | Status |
|---|---|
| Built-in structured logging (JSON) | 📋 |
| Actor lifecycle events (spawned, stopped, crashed) | 📋 |
| Mailbox depth metrics | 📋 |
| Message throughput per actor | 📋 |
| OpenTelemetry trace export | 💡 |
| Web-based actor graph visualizer | 💡 |

---

## v1.0 — Stable API

Harden the API, finalize naming, and publish to PyPI.

| Item | Status |
|---|---|
| Stable public API with deprecation policy | 📋 |
| Full type stubs (`.pyi` files) | 📋 |
| Published to PyPI as `maap` | 📋 |
| Comprehensive test suite (>85% coverage) | 📋 |
| Migration guide from v0.x | 📋 |

---

## Post v1.0 — Stretch Goals

These are ideas worth exploring once the core is stable. No timeline.

| Idea | Notes |
|---|---|
| Multi-process actor system | Actors across OS processes via IPC |
| Network transport | Actors across machines via gRPC or WebSockets |
| Persistent actor state | Snapshot and restore actor state |
| Integration with LangGraph / CrewAI | Adapter layer for existing frameworks |

---

## How to Influence the Roadmap

Open a [GitHub Discussion](https://github.com/your-username/multi-agent-actor-patterns/discussions) with your use case. Items move from 💡 to 📋 when there's demonstrated community need.
