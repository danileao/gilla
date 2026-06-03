# DevEx Golden Path Ecosystem

A shared engineering tooling platform that provides a **Golden Path** for 10+ independent, full-cycle engineering teams. Homologates the development lifecycle and reports consistent, comparable DORA metrics across polyglot teams (Python, Go, TypeScript, Clojure).

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Developer Workstation                    │
│                                                           │
│  devex check-branch  ───  pre-push hook                   │
│  devex pr-create     ───  Shift-Left validation            │
│  devex dora          ───  DORA metrics                    │
└──────────────────────┬────────────────────────────────────┘
                       │ git push
                       ▼
┌──────────────────────────────────────────────────────────┐
│                   GitHub Actions                           │
│                                                           │
│  ┌──────────────────────────────────────────┐             │
│  │  compliance-and-build                     │             │
│  │  ├─ Branch naming (check-branch)          │             │
│  │  ├─ Build steps                           │             │
│  │  ├─ Two-Reviewer Rule (SOC 2)            │             │
│  │  └─ Audit trail emission                  │             │
│  └──────────────┬───────────────────────────┘             │
│                 │ success                                  │
│  ┌──────────────▼───────────────────────────┐             │
│  │  small-tests                              │             │
│  │  ├─ Unit tests                           │             │
│  │  ├─ Property-Based Testing (optional)    │             │
│  │  └─ Contract tests (optional)            │             │
│  └──────────────┬───────────────────────────┘             │
│                 │ success                                  │
│  ┌──────────────▼───────────────────────────┐             │
│  │  deploy (matrix: sandbox/staging/prod)   │             │
│  │  ├─ PR → sandbox                         │             │
│  │  ├─ push main → staging                  │             │
│  │  └─ release tag → production             │             │
│  └──────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                   devex-framework                         │
│  TypeScript library that generates:                      │
│  ├─ .github/workflows/ci.yml                             │
│  ├─ .github/PULL_REQUEST_TEMPLATE.md                      │
│  └─ infra/cdk-stack-{env}.json                           │
└──────────────────────────────────────────────────────────┘
```

## Components

### [devex-cli](./devex-cli) — Python CLI

Primary developer interface. Enforces Git conventions, validates projects, and collects DORA metrics.

| Command | Purpose |
|---------|---------|
| `devex check-branch` | Validate branch name follows `{WORK_ID}-description` |
| `devex init` | Install pre-push git hook |
| `devex pr-create` | Create PR with Shift-Left validation + SOC 2 audit |
| `devex validate` | Run build steps from `devex.json` |
| `devex dora` | Calculate DORA metrics from GitHub API |

### [devex-framework](./devex-framework) — TypeScript Framework

Generates CI/CD pipelines, PR templates, and infrastructure definitions from a `devex.json` configuration file.

| Generator | Output |
|-----------|--------|
| `generateGitHubWorkflow` | `.github/workflows/ci.yml` |
| `generatePullRequestTemplate` | `.github/PULL_REQUEST_TEMPLATE.md` |
| `generateAwsCdkStack` | `infra/cdk-stack.json` |
| `generateAwsCdkStackForEnv` | `infra/cdk-stack-{env}.json` |

## Prerequisites

- **Node.js** 22+ and **pnpm** (`npm install -g pnpm`)

## Quick Start

### 1. Clone and setup

```bash
git clone https://github.com/danileao/gilla.git
cd gilla
pnpm install
```

### 2. Generate everything

```bash
pnpm devex-framework
```

This generates a CI/CD workflow (`.github/workflows/ci.yml`), PR template (`.github/PULL_REQUEST_TEMPLATE.md`), and CDK stacks (`infra/cdk-stack-*.json`) using the example config at `devex-framework/devex.json`.

### 3. Run tests

```bash
cd devex-framework
pnpm test
```

---

### Using as a dependency in your own project

```bash
pnpm add "devex-framework@git+https://github.com/danileao/gilla.git#subdirectory=devex-framework"
pnpm exec devex-framework
```

Create a `devex.json` at your project root to customize the output:

```json
{
    "name": "My App",
    "environment": "production",
    "buildSteps": ["pnpm install", "pnpm test"],
    "governance": {
        "enforceWorkId": true,
        "requiredApprovals": 2,
        "teamOwner": "MY_TEAM"
    },
    "environments": {
        "sandbox": { "accountId": "111111111111", "region": "us-east-1" },
        "staging": { "accountId": "222222222222", "region": "us-east-2" },
        "production": { "accountId": "333333333333", "region": "us-west-2" }
    },
    "cliSource": "git+https://github.com/danileao/gilla.git#subdirectory=devex-cli",
    "testStages": {
        "unit": "pnpm test:ci",
        "pbt": "pnpm test:pbt",
        "contract": "pnpm test:contract"
    }
}
```

### CLI (optional)

```bash
uv tool install "devex-cli@git+https://github.com/danileao/gilla.git#subdirectory=devex-cli"
devex --help
```

## DORA Metrics

The ecosystem standardizes capture of four core DORA metrics:

- **Deployment Frequency**: How often code is deployed to production
- **Lead Time for Changes**: Time from commit to production
- **Change Failure Rate**: Percentage of deployments causing failures
- **Mean Time to Recovery (MTTR)**: Time to recover from failures

Run locally: `devex dora --mock`

The CLI filters bot PRs (Dependabot, Renovate) from lead time calculations, ensuring comparable metrics across all teams regardless of automation tooling.

## CI/CD Pipelines

### PR Pipeline (triggered on `pull_request`)

1. **compliance-and-build**: Branch naming, build steps, Two-Reviewer Rule, audit trail
2. **small-tests**: Unit tests, PBT, contract validation
3. **deploy → sandbox**: Automated CDK deployment

### Integration Pipeline (triggered on `push main` / `release`)

1. **compliance-and-build**: Same governance checks
2. **small-tests**: Same test suite
3. **deploy → staging** (on merge to main)
4. **deploy → production** (on release tag)

## Governance

- **Universal Work ID**: `{WORK_ID}-description` format enforced across branches, commits, and PRs
- **Two-Reviewer Rule**: Minimum 2 approvals required before merge
- **SOC 2 Audit Trail**: Standardized logging of who, what, when, and why
- **Shift-Left Validation**: Pre-push hooks → local validation → CI enforcement

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for inner-source contribution guidelines.

## License

ISC
