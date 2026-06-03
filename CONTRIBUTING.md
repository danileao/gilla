# Contributing

This project contains two packages that form the DevEx Golden Path ecosystem:

- `devex-cli/` — Python CLI for governance, validation, and DORA metrics
- `devex-framework/` — TypeScript framework for generating CI/CD pipelines and infrastructure

## Development Setup

### Prerequisites

- Python 3.11+ with `uv` (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Node.js 22+ with `pnpm` (`npm install -g pnpm`)

### devex-cli

```bash
cd devex-cli
uv sync
uv run pytest
```

### devex-framework

```bash
cd devex-framework
pnpm install
pnpm build
pnpm test
```

## Pull Request Process

1. Create a branch named `{WORK_ID}-short-description` from `main`
2. Make your changes
3. Run all tests locally
4. Create a PR using `devex pr-create` or the GitHub UI
5. Ensure the PR template is filled out with SOC 2 audit information
6. Two reviewers must approve before merge

The CI pipeline enforces:
- Branch naming compliance (`check-branch`)
- Two-Reviewer Rule (SOC 2)
- Build steps and tests pass
- Shift-Left validation (`devex validate`)

## Code Style

### Python (devex-cli)

- Type hints on all function signatures
- Snake case for functions and variables
- Docstrings on public functions (Google style)
- Tests in `tests/` using pytest

### TypeScript (devex-framework)

- TypeScript strict mode
- Camel case for functions and variables
- Interfaces for all configuration types
- Tests alongside source in `src/tests/` using Vitest

## Release Process

1. Update `devex.json` in consumer projects with the new version tag
2. Tag the release: `git tag v0.x.x && git push origin v0.x.x`
3. Run `devex dora` to confirm metrics before promoting
