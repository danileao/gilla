import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as fs from 'node:fs';
import { DevExGenerator } from '../core/generator.js';
import { GitHubWorkflowConfig, AwsCdkConfig, TestStages } from '../types/index.js';

vi.mock('fs', () => ({
    existsSync: vi.fn(),
    mkdirSync: vi.fn(),
    writeFileSync: vi.fn(),
}));

describe('DevExGenerator - Core Workflow & Infrastructure Engine', () => {
    let generator: DevExGenerator;

    beforeEach(() => {
        generator = new DevExGenerator();
        vi.clearAllMocks();
    });

    it('should successfully build a SOC 2 compliant GitHub Actions workflow', () => {
        const mockConfig: GitHubWorkflowConfig = {
            name: "Core Pipeline Test",
            environment: "staging",
            buildSteps: ["pnpm test"],
            governance: {
                enforceWorkId: true,
                requiredApprovals: 2,
                teamOwner: "BNK",
            },
        };

        vi.mocked(fs.existsSync).mockReturnValue(false);

        const outputPath = generator.generateGitHubWorkflow(mockConfig, './dummy-dir');

        expect(outputPath).toContain('ci.yml');
        expect(fs.mkdirSync).toHaveBeenCalledWith('./dummy-dir', { recursive: true });

        const [writtenPath, content] = vi.mocked(fs.writeFileSync).mock.calls[0];
        expect(writtenPath).toContain('ci.yml');

        expect(content).toContain('pip install uv');
        expect(content).toContain('uv pip install -e ./devex-cli');
        expect(content).toContain('devex check-branch');
        expect(content).toContain('TEAM OWNER: BNK');
        expect(content).toContain('TARGET ENVIRONMENT: staging');
        expect(content).toContain('Two-Reviewer Rule');
        expect(content).toContain('required: 2');
    });

    it('should include Amazon Q Developer step when aiReview is enabled', () => {
        const mockConfig: GitHubWorkflowConfig = {
            name: "AI Review Test",
            environment: "production",
            buildSteps: ["pnpm test"],
            governance: {
                enforceWorkId: true,
                requiredApprovals: 2,
                teamOwner: "FIN",
            },
            aiReview: true,
        };

        vi.mocked(fs.existsSync).mockReturnValue(false);

        generator.generateGitHubWorkflow(mockConfig, './dummy-dir');

        const [, content] = vi.mocked(fs.writeFileSync).mock.calls[0];
        expect(content).toContain('Amazon Q Developer Code Review');
        expect(content).toContain('aws/amazon-q-developer-action@v1');
        expect(content).toContain('analysis-types: security,quality,governance');
    });

    it('should skip Amazon Q Developer step when aiReview is not set', () => {
        const mockConfig: GitHubWorkflowConfig = {
            name: "No AI Review",
            environment: "production",
            buildSteps: ["pnpm test"],
            governance: {
                enforceWorkId: true,
                requiredApprovals: 2,
                teamOwner: "FIN",
            },
        };

        vi.mocked(fs.existsSync).mockReturnValue(false);

        generator.generateGitHubWorkflow(mockConfig, './dummy-dir');

        const [, content] = vi.mocked(fs.writeFileSync).mock.calls[0];
        expect(content).not.toContain('Amazon Q Developer Code Review');
    });

    it('should install CLI from git source when cliSource is configured', () => {
        const mockConfig: GitHubWorkflowConfig = {
            name: "Git Install Test",
            environment: "production",
            buildSteps: ["echo ok"],
            governance: {
                enforceWorkId: true,
                requiredApprovals: 2,
                teamOwner: "FIN",
            },
            cliSource: "git+https://github.com/org/devex-cli@v0.1.0",
        };

        vi.mocked(fs.existsSync).mockReturnValue(false);

        generator.generateGitHubWorkflow(mockConfig, './dummy-dir');

        const [, content] = vi.mocked(fs.writeFileSync).mock.calls[0];
        expect(content).toContain('pip install "devex-cli@git+https://github.com/org/devex-cli@v0.1.0"');
        expect(content).toContain('devex check-branch');
        expect(content).not.toContain('uv pip install -e');
    });

    it('should generate deployment stages when environments are configured', () => {
        const mockConfig: GitHubWorkflowConfig = {
            name: "Multi-Env Pipeline",
            environment: "production",
            buildSteps: ["pnpm test"],
            governance: {
                enforceWorkId: true,
                requiredApprovals: 2,
                teamOwner: "FIN",
            },
            environments: {
                sandbox: { accountId: "111111111111", region: "us-east-1" },
                staging: { accountId: "222222222222", region: "us-east-2" },
                production: { accountId: "333333333333", region: "us-west-2" },
            },
        };

        vi.mocked(fs.existsSync).mockReturnValue(false);

        generator.generateGitHubWorkflow(mockConfig, './dummy-dir');

        const [, content] = vi.mocked(fs.writeFileSync).mock.calls[0];
        expect(content).toContain('deploy');
        expect(content).toContain('sandbox');
        expect(content).toContain('staging');
        expect(content).toContain('production');
        expect(content).toContain('Environment Promotion');
        expect(content).toContain('matrix.environment');
        expect(content).not.toContain('small-tests');
    });

    it('should generate per-environment AWS CDK stacks with proper naming', () => {
        const mockCdkConfig: AwsCdkConfig = {
            stackName: "TransactionifySandboxStack",
            region: "us-east-1",
            accountId: "111111111111",
            environment: "production",
            governance: {
                enforceWorkId: true,
                requiredApprovals: 2,
                teamOwner: "FIN",
            },
        };

        vi.mocked(fs.existsSync).mockReturnValue(false);

        const outputPath = generator.generateAwsCdkStackForEnv(mockCdkConfig, 'sandbox', './dummy-infra');

        expect(outputPath).toContain('cdk-stack-sandbox.json');
        expect(fs.mkdirSync).toHaveBeenCalledWith('./dummy-infra', { recursive: true });

        const [, jsonContent] = vi.mocked(fs.writeFileSync).mock.calls[0];
        const parsedPayload = JSON.parse(jsonContent as string);

        expect(parsedPayload.resourceTags.Environment).toBe('sandbox');
        expect(parsedPayload.resourceTags.TeamOwner).toBe('FIN');
        expect(parsedPayload.resourceTags.ManagedBy).toBe('DevExGoldenPathFramework');
        expect(parsedPayload.awsMetadata.region).toBe('us-east-1');
        expect(parsedPayload.awsMetadata.accountId).toBe('111111111111');
    });

    it('should generate a standardized PR template with governance sections', () => {
        const mockConfig: GitHubWorkflowConfig = {
            name: "Test",
            environment: "production",
            buildSteps: ["echo ok"],
            governance: {
                enforceWorkId: true,
                requiredApprovals: 2,
                teamOwner: "FIN",
            },
        };

        vi.mocked(fs.existsSync).mockReturnValue(false);

        const outputPath = generator.generatePullRequestTemplate(mockConfig, './.github');

        expect(outputPath).toContain('PULL_REQUEST_TEMPLATE.md');
        const [, content] = vi.mocked(fs.writeFileSync).mock.calls[0];
        expect(content).toContain('{WORK_ID}');
        expect(content).toContain('SOC 2');
        expect(content).toContain('Two-Reviewer Rule');
        expect(content).toContain('FIN');
    });

    it('should generate small-tests job with Unit, PBT, and Contract stages when testStages is configured', () => {
        const testStages: TestStages = {
            unit: "pnpm test:ci",
            pbt: "pnpm test:pbt",
            contract: "pnpm test:contract",
        };
        const mockConfig: GitHubWorkflowConfig = {
            name: "Small-Tests Pipeline",
            environment: "production",
            buildSteps: ["pnpm build"],
            governance: {
                enforceWorkId: true,
                requiredApprovals: 2,
                teamOwner: "FIN",
            },
            environments: {
                sandbox: { accountId: "111111111111", region: "us-east-1" },
                staging: { accountId: "222222222222", region: "us-east-2" },
                production: { accountId: "333333333333", region: "us-west-2" },
            },
            testStages,
        };

        vi.mocked(fs.existsSync).mockReturnValue(false);

        generator.generateGitHubWorkflow(mockConfig, './dummy-dir');

        const [, content] = vi.mocked(fs.writeFileSync).mock.calls[0];

        expect(content).toContain('small-tests');
        expect(content).toContain('Small Tests (Unit · PBT · Contract)');
        expect(content).toContain('Unit Tests');
        expect(content).toContain('pnpm test:ci');
        expect(content).toContain('Property-Based Testing');
        expect(content).toContain('pnpm test:pbt');
        expect(content).toContain('API Contract Validation');
        expect(content).toContain('pnpm test:contract');
        expect(content).toContain('needs: [ compliance-and-build, small-tests ]');
    });

    it('should generate small-tests job with only Unit when pbt and contract are omitted', () => {
        const testStages: TestStages = {
            unit: "go test ./...",
        };
        const mockConfig: GitHubWorkflowConfig = {
            name: "Minimal Tests",
            environment: "development",
            buildSteps: ["make build"],
            governance: {
                enforceWorkId: false,
                requiredApprovals: 2,
                teamOwner: "ENG",
            },
            testStages,
        };

        vi.mocked(fs.existsSync).mockReturnValue(false);

        generator.generateGitHubWorkflow(mockConfig, './dummy-dir');

        const [, content] = vi.mocked(fs.writeFileSync).mock.calls[0];

        expect(content).toContain('small-tests');
        expect(content).toContain('Small Tests (Unit)');
        expect(content).toContain('Unit Tests');
        expect(content).toContain('go test ./...');
        expect(content).not.toContain('Property-Based Testing');
        expect(content).not.toContain('API Contract Validation');
        expect(content).toContain('needs: [ compliance-and-build, small-tests ]');
    });
});
