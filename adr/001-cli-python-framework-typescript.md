# ADR-001: CLI in Python, Framework in TypeScript

**Status:** Accepted  
**Date:** 2026-06-02  
**Author:** DevEx Platform Team

## Context

The DevEx Golden Path ecosystem needs two components:
1. A CLI tool that developers run locally and in CI for governance enforcement
2. A framework that generates CI/CD pipelines, PR templates, and infrastructure definitions

The target users are TypeScript/Node.js development teams.

## Decision

### CLI: Python with `uv` distribution

- Python 3.11+ with `typer` for CLI, `rich` for terminal output, `gitpython` for git operations
- Distributed via `uv tool install` (PyPI-compatible, no runtime dependency on Python for consumers)
- Installed as a global `devex` command
- `uv` is faster than `pip` and handles isolated environments

Rationale: Python has mature CLI libraries, strong git integration, and universal package distribution. `uv` eliminates the "Python is not installed" excuse.

### Framework: TypeScript with `pnpm`

- TypeScript compiled to JS, distributed via npm
- `pnpm` for package management (faster than npm, strict dependency resolution)
- Consumer projects import the generator classes directly

Rationale: Aligns with the target TypeScript ecosystem. Matches the consumer's build toolchain.

## Consequences

- Developers installing the CLI need `uv` (one-time setup)
- `uv` is not pre-installed on GitHub Actions runners — the workflow installs it via `pip install uv`
- Framework consumers need `pnpm` in their CI — handled by `pnpm/action-setup@v4`
- Two different languages means duplicated patterns (e.g., branch checking logic exists only in the CLI)
