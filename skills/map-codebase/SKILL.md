---
name: map-codebase
description: Explore a repository and generate or update AGENTS.md with architecture, stack, conventions, and operational guidance for coding agents. Use when docs are missing or stale.
compatibility: Requires filesystem read/write access in target repository.
metadata:
  invocation: user-or-orchestrator
---

# map-codebase

Explore the current project and write findings to `AGENTS.md`.

## Protocol

1. Inspect structure and key config files (`pyproject.toml`, `package.json`, `go.mod`, etc.).
2. Identify stack, build/run/test commands, and architecture boundaries.
3. Capture project conventions, testing strategy, and deployment clues.
4. Write a practical agent-oriented summary in `AGENTS.md`.
5. If `AGENTS.md` exists, merge with current content (do not blindly overwrite useful sections).

## Suggested sections

- Project overview
- Build and test commands
- Architecture and module structure
- Code style and conventions
- Testing guidance
- Security considerations
- Key dependencies
- Known constraints
