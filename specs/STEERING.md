# DevEx Golden Path — Steering Document

## Context for AI-Generated Reviews

This steering document provides Amazon Q Developer and other AI coding agents with the organizational context needed to perform automated PR reviews aligned with the DevEx Golden Path standards.

## Review Criteria

### 1. Branch Naming Compliance
Every PR branch MUST match `^[A-Z]{3}-\d+-[a-z0-9-]+$`.
- Allowed bypass branches: `main`, `master`, `development`, `dev`
- Any deviation MUST be flagged with `❌ Branch naming violation`

### 2. Work ID in PR Title
PR title MUST contain a Work ID (e.g., `FIN-123`).
- Format: `{WORK_ID}: {description}`
- If missing: flag and suggest correction

### 3. Code Quality Checks
- Python (`devex-cli`): Type hints required on all public functions, snake_case naming, docstrings on public APIs
- TypeScript (`devex-framework`): Strict mode required, camelCase, interfaces over types for configuration objects

### 4. SOC 2 Compliance
Every PR MUST include:
- DORA Impact assessment
- Testing checklist (unit + integration + manual)
- Team ownership information
- Required approvals count

### 5. DORA Metric Impact
Review MUST consider whether a change will affect:
- Deployment Frequency (does this add/remove deployment steps?)
- Lead Time (does this change the build/test pipeline?)
- Change Failure Rate (does this introduce risk?)
- MTTR (does this improve observability/recovery?)

## AI Behavior Guidelines

When conducting automated reviews, Amazon Q Developer SHOULD:

1. **Prioritize governance violations** over code style nits
2. **Block** PRs that violate branch naming or Work ID requirements
3. **Comment** on missing SOC 2 sections in PR descriptions
4. **Approve** only when all governance checks pass AND code quality meets team standards
5. **Never override** the Two-Reviewer Rule — AI review complements, not replaces, human review

## File Patterns

| Pattern | Relevant Rules |
|---------|----------------|
| `devex-cli/**/*.py` | Python type hints, snake_case, pytest |
| `devex-framework/src/**/*.ts` | TypeScript strict mode, camelCase, Vitest |
| `**/devex.json` | Validate against config schema |
| `**/*.md` | Check for SOC 2 compliance sections |
