# Changelog

All notable changes to this project will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

Changes that are merged to `dev` but not yet released.

---

## [0.2.0] — 2026-04-06

### Added
- **Bounded mailbox** with configurable capacity and backpressure (`MailboxFullError`).
- **Restart budget** — supervisors limit restarts to `max_restarts` within a `restart_window`; auto-escalates on exhaustion.
- **Actor lifecycle hooks**: `pre_start()`, `post_stop()`, `pre_restart()`.
- **Graceful shutdown** — `ActorSystem.shutdown()` and async context manager (`async with ActorSystem()`).
- **Address validation** — actor addresses are validated against a strict pattern at creation time.
- **Custom exception hierarchy**: `MaapError`, `MailboxFullError`, `InvalidAddressError`, `RestartBudgetExhaustedError`, `SystemShutdownError`.
- **Actor observability**: `uptime`, `message_count`, `total_enqueued`, `total_processed` properties.
- **Mailbox `drain()`** method for shutdown cleanup.
- `py.typed` marker (PEP 561) for typed consumers.
- `SECURITY.md` with responsible disclosure policy.
- `.env.example` for safe credential management.
- GitHub Actions CI workflow (lint + test across Python 3.10–3.13).
- New tests: bounded mailbox, lifecycle hooks, graceful shutdown, address validation, restart budget exhaustion.
- Comprehensive `pyproject.toml` with ruff, mypy, coverage configuration.
- Full README overhaul with architecture diagrams, quickstart, and security section.

### Changed
- **BREAKING**: `ResearchSupervisor` no longer exported from `maap.__init__` (import from `maap.examples.research_agent.supervisor` directly).
- Supervisor `STOP` and `ESCALATE` strategies now use `stop_actor()` (graceful) instead of `terminate()` (fire-and-forget).
- Dead letter actor now logs message types instead of raw message contents (prevents credential leaks).
- Error messages in `ActorFailed` truncated to 4096 chars to prevent log bloat.
- Worker uses configurable LLM model via `MAAP_LLM_MODEL` env var (default: `claude-sonnet-4-20250514`).
- Actor failure logs no longer include `%r` of the message (prevents logging sensitive data).

### Fixed
- **Infinite restart loop bug** — perpetually failing actors now correctly exhaust the restart budget and escalate.
- **Race condition in `terminate()`** — fire-and-forget stop is now documented; `stop_actor()` added as the safe alternative.
- **Memory leak** — old actor instances are now properly cleaned from registry on restart.
- **API key leak risk** — Anthropic exceptions no longer logged with full message (could contain key in URL).

### Security
- Bounded mailboxes prevent memory exhaustion (DoS vector).
- Actor address validation prevents injection via crafted addresses.
- Restart budgets prevent infinite restart loop resource exhaustion.
- Log sanitization: no `%r` of messages, error strings truncated.
- Added `SECURITY.md` with disclosure policy and security design principles.

### Removed
- Duplicate `docs/LICENSE` file (use root `LICENSE` only).

---

## [0.1.0] — 2026-03-01

### Added
- Initial project scaffold
- Core `Actor` base class with async mailbox
- `ActorSystem` with registry and asyncio scheduler
- `SupervisorActor` with RESTART strategy
- `DeadLetterActor` with structured logging
- Typed `Message` base class with Pydantic validation
- Research Agent example: supervisor → workers → reconciliation
- README, ARCHITECTURE, CONTRIBUTING, ROADMAP, CODE_OF_CONDUCT, LICENSE

---

## Format Reference

Each release entry uses these sections (omit empty ones):

```
## [x.y.z] — YYYY-MM-DD

### Added
- New features or capabilities

### Changed
- Changes to existing behavior (non-breaking)

### Deprecated
- Features that will be removed in a future version

### Removed
- Features removed in this version

### Fixed
- Bug fixes

### Security
- Security vulnerability fixes
```

---

[Unreleased]: https://github.com/your-username/multi-agent-actor-patterns/compare/main...dev
