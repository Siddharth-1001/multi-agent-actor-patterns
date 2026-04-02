# Contributing to multi-agent-actor-patterns

Thank you for your interest in contributing. This guide covers everything you need to go from idea to merged PR.

---

## Before You Start

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the design constraints. PRs that introduce shared state or silent failure will not be merged — not because they are wrong in general, but because they conflict with the explicit goals of this project.
- Check [open issues](https://github.com/your-username/multi-agent-actor-patterns/issues) before opening a new one. Your idea may already be tracked.
- For significant changes (new abstractions, breaking API changes), open a **discussion issue first** before writing code. This saves everyone time.

---

## Ways to Contribute

- **Bug reports** — open an issue with a minimal reproduction
- **Bug fixes** — reference the issue in your PR
- **New examples** — demonstrate a new actor pattern or agent topology
- **Documentation** — improve clarity, fix errors, add diagrams
- **Core features** — see [ROADMAP.md](ROADMAP.md) for planned work

---

## Development Setup

```bash
# Clone the repo
git clone https://github.com/your-username/multi-agent-actor-patterns.git
cd multi-agent-actor-patterns

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests to confirm everything works
pytest
```

---

## Branching

| Branch | Purpose |
|---|---|
| `main` | Stable, always releasable |
| `dev` | Integration branch for new features |
| `feature/<name>` | Your feature branch, cut from `dev` |
| `fix/<issue-number>` | Bug fix branch, cut from `main` |

```bash
# For a new feature
git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name

# For a bug fix
git checkout main
git pull origin main
git checkout -b fix/123-describe-the-bug
```

---

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer: closes #issue]
```

**Types:**

| Type | When to use |
|---|---|
| `feat` | New feature or behavior |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change with no behavior change |
| `test` | Adding or updating tests |
| `chore` | Tooling, dependencies, CI |

**Examples:**
```
feat(supervisor): add ESCALATE restart strategy
fix(dead-letter): prevent duplicate delivery on retry
docs(architecture): add message flow diagram for research agent
test(mailbox): add test for overflow behavior
```

---

## Code Standards

- **Python 3.10+** — use `match` statements, `|` union types, and structural pattern matching where appropriate
- **Type hints everywhere** — all public functions and class attributes must be typed
- **Async-first** — actor message handlers must be `async def`
- **No shared mutable state** — if a review comment says "this actor is reading another actor's state", the PR will be held until fixed
- **Pydantic for messages** — all `Message` subclasses use Pydantic validation

**Formatter / linter:**
```bash
ruff check .       # linting
ruff format .      # formatting
mypy maap/         # type checking
```

All three must pass before a PR is reviewable.

---

## Testing

All new behavior requires tests. The test layout mirrors the source:

```
tests/
├── core/
│   ├── test_actor.py
│   ├── test_supervisor.py
│   └── test_dead_letter.py
└── examples/
    └── test_research_agent.py
```

```bash
pytest                        # all tests
pytest tests/core/            # core only
pytest -k "test_supervisor"   # by name
pytest --cov=maap             # with coverage
```

Coverage target: **80% minimum** for core modules.

---

## Opening a Pull Request

1. Push your branch to your fork
2. Open a PR against `dev` (not `main`)
3. Fill in the PR template — describe what changed and why
4. Link any relevant issues (`Closes #123`)
5. Ensure all CI checks pass
6. Request a review

**PR title format** (same as commit messages):
```
feat(supervisor): add ESCALATE restart strategy
```

**What reviewers look for:**
- Does this respect the no-shared-state constraint?
- Is the new message type documented?
- Are failure paths explicit (not swallowed)?
- Are tests present and meaningful?

---

## Reporting Bugs

Open an issue with:

- Python version and OS
- Minimal code to reproduce the bug
- What you expected to happen
- What actually happened (include full traceback)

---

## Questions

Open a [GitHub Discussion](https://github.com/your-username/multi-agent-actor-patterns/discussions) for design questions or ideas. Issues are for bugs and tracked work.
