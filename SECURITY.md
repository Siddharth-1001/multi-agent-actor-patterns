# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please report them responsibly:

1. **Email**: Send details to the maintainer(s) listed in `pyproject.toml`.
2. **GitHub Private Advisory**: Use [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories) to report privately.

### What to include

- A description of the vulnerability and its potential impact.
- Steps to reproduce or a proof-of-concept.
- Any suggested fix or mitigation.

### Response timeline

- **Acknowledgment**: Within 48 hours.
- **Initial assessment**: Within 5 business days.
- **Fix or advisory**: Within 30 days for critical issues.

## Security Design Principles

MAAP follows these security principles:

1. **No shared mutable state** — Actors communicate only via immutable messages.
2. **Bounded resources** — Mailboxes have configurable capacity limits to prevent memory exhaustion.
3. **Input validation** — Actor addresses are validated against a strict allowlist pattern.
4. **No secrets in logs** — Error messages are truncated; API keys are never logged.
5. **Fail-safe supervision** — Restart budgets prevent infinite restart loops.
6. **Graceful degradation** — Undeliverable messages go to the dead letter actor, not silently dropped.

## Known Considerations

- MAAP is **single-process, single-node**. It does not provide network-level security, TLS, or authentication between distributed actors.
- Message payloads of type `Any` are accepted for flexibility. In production, use typed Pydantic messages and avoid passing untrusted objects.
- The research agent example uses an external API (Anthropic). Ensure API keys are stored in environment variables, never in code or config files.
