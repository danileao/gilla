# DevEx Framework

TypeScript framework for generating SOC 2 compliant CI/CD pipelines, PR templates, and CDK infrastructure stacks.

## Installation

```bash
pnpm add "devex-framework@git+https://github.com/danileao/gilla.git#subdirectory=devex-framework"
```

## Usage

### Generate a CI workflow

```typescript
import { DevExGenerator } from 'devex-framework';

const gen = new DevExGenerator();

gen.generateGitHubWorkflow({
    name: 'My App CI',
    environment: 'production',
    buildSteps: ['pnpm install', 'pnpm test:ci'],
    governance: {
        enforceWorkId: true,
        requiredApprovals: 2,
        teamOwner: 'MY_TEAM'
    },
    cliSource: 'git+https://github.com/danileao/gilla.git#subdirectory=devex-cli',
    environments: {
        sandbox: { accountId: '111111111111', region: 'us-east-1' },
        staging: { accountId: '222222222222', region: 'us-east-2' },
        production: { accountId: '333333333333', region: 'us-west-2' }
    },
    testStages: {
        unit: 'pnpm test:ci',
        pbt: 'pnpm test:pbt',
        contract: 'pnpm test:contract'
    }
});
```

Output: `.github/workflows/ci.yml`

### Generate a PR template

```typescript
gen.generatePullRequestTemplate({
    governance: {
        enforceWorkId: true,
        requiredApprovals: 2,
        teamOwner: 'MY_TEAM'
    }
});
```

Output: `.github/PULL_REQUEST_TEMPLATE.md`

### Generate CDK stacks

```typescript
gen.generateAwsCdkStack({
    stackName: 'my-app',
    environment: 'production',
    region: 'us-west-2',
    accountId: '333333333333',
    governance: {
        enforceWorkId: true,
        requiredApprovals: 2,
        teamOwner: 'MY_TEAM'
    }
});
```

Output: `infra/cdk-stack.json`

## What the generator creates

### CI Workflow (`ci.yml`)

| Event | Jobs | Deploys to |
|-------|------|------------|
| `pull_request` | compliance-and-build + small-tests | sandbox |
| `push` to main | compliance-and-build + small-tests + deploy | staging |
| `release` published | compliance-and-build + small-tests + deploy | production |

The workflow enforces:
- Branch naming convention (`WORK_ID-description`)
- Two-Reviewer Rule (SOC 2)
- Build steps validation
- Shift-Left validation via `devex validate`
- Stack-aware deployment per environment
- Audit trail emission

### Test Stages

Three test stages are supported:
- `unit` — traditional unit tests
- `pbt` — property-based testing (optional)
- `contract` — API contract validation (optional)

These run in a separate `small-tests` job that the deploy job depends on.

## Configuration Reference

A `devex.json` in the consumer project enables CLI commands like `devex validate` and `devex dora`. Full schema:

```json
{
    "name": "Project Name",
    "environment": "production",
    "buildSteps": ["command1", "command2"],
    "governance": {
        "enforceWorkId": true,
        "requiredApprovals": 2,
        "teamOwner": "TEAM_NAME"
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

## Development

```bash
git clone https://github.com/danileao/gilla.git
cd gilla/devex-framework
pnpm install
pnpm build
pnpm test
```
