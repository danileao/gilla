# DevEx CLI

Golden Path CLI that enforces Git governance, DORA metrics, SOC 2 audit trails, and quality gates.

## Installation

```bash
uv tool install "devex-cli@git+https://github.com/danileao/gilla.git#subdirectory=devex-cli"
```

Verify:

```bash
devex --help
```

## Commands

### `devex check-branch`

Verify the current branch follows the `{WORK_ID}-description` naming convention. Used in CI and pre-push hooks.

```bash
devex check-branch
```

Allows bypass branches: `main`, `master`, `development`, `dev`.

### `devex init`

Install a pre-push git hook that runs `check-branch` and `validate` before every push.

```bash
devex init
```

### `devex pr-create`

Create a pull request with Shift-Left validation (branch check + build steps), SOC 2 template, and optional reviewer assignments.

```bash
devex pr-create --title "COR-123: Add payment gateway" --reviewer user1 --reviewer user2
```

### `devex validate`

Run the build steps defined in `devex.json` to validate the project before committing.

```bash
devex validate
```

### `devex dora`

Calculate DORA metrics (Deployment Frequency, Lead Time for Changes, Change Failure Rate, MTTR) from GitHub API data.

```bash
export GITHUB_TOKEN=ghp_xxx
devex dora --owner myteam --repo myapp --days 30
devex dora --mock                          # demo mode
```

Filters out bot PRs (Dependabot, Renovate) from lead time calculations. Saves raw metrics to `dora-metrics.json`.

## Configuration

Add a `devex.json` at the project root:

```json
{
    "name": "My App",
    "environment": "production",
    "buildSteps": ["npm install", "npm test"],
    "governance": {
        "enforceWorkId": true,
        "requiredApprovals": 2,
        "teamOwner": "MY_TEAM"
    }
}
```

## CI Integration

The CLI is designed to run in GitHub Actions. Use `cliSource` in `devex.json` to pin a version:

```json
"cliSource": "git+https://github.com/danileao/gilla.git#subdirectory=devex-cli"
```

The generated workflow installs it automatically.

## Development

```bash
git clone https://github.com/danileao/gilla.git
cd gilla/devex-cli
uv sync
devex dora --mock
```

Run tests:

```bash
uv run pytest
```
