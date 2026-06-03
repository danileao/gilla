# DevEx Golden Path — System Specification

## Purpose

This document serves as the authoritative spec for AI-assisted development of the DevEx Golden Path ecosystem. It provides the context required for tools like Amazon Q Developer and Kiro to generate, review, and maintain code consistently.

## System Overview

The DevEx Golden Path ecosystem consists of three packages:
1. **devex-cli** (Python) — developer workstation governance CLI
2. **devex-framework** (TypeScript) — CI/CD and infrastructure code generator
3. **transactionify-api** — consumer reference project

## Core Concepts

### Universal Work ID
All branches, commits, and PRs MUST follow the pattern `{WORK_ID}-description` where `WORK_ID` matches `^[A-Z]{3}-\d+$` (e.g., `FIN-123-add-payment-gateway`).

### Two-Reviewer Rule
Every PR requires exactly 2 approved reviews before merge. Enforced in CI via GitHub API.

### DORA Metrics
Four metrics are collected standardized across all teams:
- Deployment Frequency (deploys/month)
- Lead Time for Changes (hours from commit to production)
- Change Failure Rate (% of deployments causing failures)
- Mean Time to Recovery (hours)

Bot PRs (Dependabot, Renovate) are filtered from lead time calculations.

### Pipeline Stages

#### PR Pipeline (pull_request event)
1. compliance-and-build → 2. small-tests → 3. deploy (sandbox only)

#### Integration Pipeline (push to main / release)
1. compliance-and-build → 2. small-tests → 3. deploy (staging on main, production on tag)

### Environments

| Environment | Trigger | Deploy Target |
|-------------|---------|---------------|
| sandbox | pull_request | PR validation |
| staging | push to main | Integration |
| production | release tag v* | Production |

## Configuration Schema (devex.json)

```typescript
interface DevExConfig {
    name: string;                    // Project name
    environment: string;             // target environment
    buildSteps: string[];            // commands to build/test
    governance: {
        enforceWorkId: boolean;
        requiredApprovals: number;   // default: 2
        teamOwner: string;           // e.g., "FIN"
    };
    environments?: {
        [env: string]: {
            accountId: string;
            region: string;
        };
    };
    cliSource?: string;              // git URL for CLI install in CI
    testStages?: {
        unit: string;                // required
        pbt?: string;                // property-based testing
        contract?: string;           // API contract validation
    };
}
```

## API Contracts

### CLI Commands

| Command | Args | Exit Code | Side Effects |
|---------|------|-----------|--------------|
| `check-branch` | none | 0=pass, 1=fail | None |
| `init` | none | 0=success | Writes `.git/hooks/pre-push` |
| `pr-create` | --title, --reviewer | 0=created | Pushes branch, creates GH PR |
| `validate` | none | 0=pass, 1=fail | Runs subprocesses per buildSteps |
| `dora` | --owner, --repo, --days, --mock | 0=done | Writes `dora-metrics.json` |

### Framework Generators

| Generator | Input | Output | File |
|-----------|-------|--------|------|
| `generateGitHubWorkflow` | GitHubWorkflowConfig | YAML | `.github/workflows/ci.yml` |
| `generatePullRequestTemplate` | GovernanceConfig | Markdown | `.github/PULL_REQUEST_TEMPLATE.md` |
| `generateAwsCdkStack` | AwsCdkConfig | JSON | `infra/cdk-stack.json` |
| `generateAwsCdkStackForEnv` | AwsCdkConfig + envName | JSON | `infra/cdk-stack-{env}.json` |

## Security & Compliance

- SOC 2 audit trail emitted on every CI run (who, what, when, why)
- Two-Reviewer Rule enforced via GitHub API
- Branch naming enforced both locally (pre-push hook) and in CI
- All metrics stored as JSON for external audit tooling
