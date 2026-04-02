# Changelog

All notable changes to this project will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

Changes that are merged to `dev` but not yet released.

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
