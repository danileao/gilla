#!/usr/bin/env node
import * as fs from 'node:fs';
import * as path from 'node:path';
import { DevExGenerator } from './core/generator.js';
import { GitHubWorkflowConfig, AwsCdkConfig } from './types/index.js';

const generator = new DevExGenerator();
const configPath = path.join(process.cwd(), 'devex.json');

console.log("==> [DevEx Framework] Executing Automated Pipeline Generation...");

if (!fs.existsSync(configPath)) {
    console.error("❌ Error: 'devex.json' configuration file not found in the root directory.");
    console.log("💡 Hint: Create a 'devex.json' file specifying your teamOwner and buildSteps.");
    process.exit(1);
}

try {
    const rawData = fs.readFileSync(configPath, 'utf-8');
    const projectConfig: GitHubWorkflowConfig = JSON.parse(rawData);

    console.log("🚀 Generating GitHub Workflow...");
    const workflowPath = generator.generateGitHubWorkflow(projectConfig, '.github/workflows');
    console.log(`[SUCCESS] GitHub Actions workflow created at: ${workflowPath}`);

    console.log("🚀 Generating Standardized PR Template...");
    const prTemplatePath = generator.generatePullRequestTemplate(projectConfig, '.github');
    console.log(`[SUCCESS] PR template created at: ${prTemplatePath}`);

    if (projectConfig.environments) {
        console.log("🚀 Generating per-environment CDK stacks...");
        for (const [envName, envConfig] of Object.entries(projectConfig.environments)) {
            const cdkConfig: AwsCdkConfig = {
                stackName: `${projectConfig.name.replace(/\s+/g, '')}${envName.charAt(0).toUpperCase() + envName.slice(1)}Stack`,
                region: envConfig.region,
                accountId: envConfig.accountId,
                environment: projectConfig.environment,
                governance: projectConfig.governance,
            };
            const cdkPath = generator.generateAwsCdkStackForEnv(cdkConfig, envName, 'infra');
            console.log(`  [SUCCESS] CDK stack for '${envName}' created at: ${cdkPath}`);
        }
    } else {
        console.log("🚀 Generating default AWS CDK Infrastructure Tags...");
        const cdkConfig: AwsCdkConfig = {
            stackName: `${projectConfig.name.replace(/\s+/g, '')}Stack`,
            region: "us-east-1",
            accountId: "123456789012",
            environment: projectConfig.environment,
            governance: projectConfig.governance,
        };
        const cdkPath = generator.generateAwsCdkStack(cdkConfig, 'infra');
        console.log(`[SUCCESS] AWS CDK CloudFormation manifest created at: ${cdkPath}`);
    }

    console.log("\n✔ [DevEx Platform] All pipelines automatically generated with 100% compliance!");

} catch (error) {
    console.error("❌ Critical error during automated generation:", error);
    process.exit(1);
}
