# ADR-003: CI/CD Pipeline Architecture

**Status:** Accepted  
**Date:** 2026-06-02  
**Author:** DevEx Platform Team

## Context

The generated CI/CD pipeline must enforce governance, run tests, and deploy to multiple environments — all while maintaining SOC 2 compliance and producing an audit trail.

## Decision

### Three-job pipeline

1. `compliance-and-build` — governance checks (branch naming, Two-Reviewer Rule), build steps, audit trail
2. `small-tests` — unit, property-based, and contract tests (optional, configurable)
3. `deploy` — matrix job deploying to sandbox/staging/production based on trigger

Deploy depends on both preceding jobs passing.

### Trigger-based deployment

| Environment | Condition |
|-------------|-----------|
| Sandbox | `pull_request` event |
| Staging | `refs/heads/main` (push/merge) |
| Production | `refs/tags/v*` (release publish) |

This ensures code is validated in sandbox before merging, automatically promoted to staging on merge, and released to production on tag.

### Shift-Left validation

- `devex check-branch` runs in CI to enforce branch naming
- `devex pr-create` runs validation locally before creating the PR
- Pre-push hook (installed via `devex init`) prevents non-compliant pushes

### Two-Reviewer Rule

- Enforced only on `pull_request` events (not on push/release)
- Queries GitHub API for approved reviews
- Blocks the pipeline if fewer than `requiredApprovals` approvals are present

## Consequences

- Sandbox deployments happen on every PR push — may incur costs
- Staging deployment is automatic on merge — no manual gate
- Production requires a tag — prevents accidental deployment
- Shift-Left validation catches issues before CI even runs
- Audit trail is emitted on every successful compliance run
