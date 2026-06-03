"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const generator_js_1 = require("./core/generator.js");
// 1. Initialize the core platform engine
const generator = new generator_js_1.DevExGenerator();
console.log("==> [DevEx Platform] Bootstrapping type-safe configuration generation...");
// 2. Define a compliant GitHub Actions Workflow configuration for Transactionify
const githubProjectConfig = {
    name: "Transactionify Core CI",
    environment: "production",
    buildSteps: [
        "pnpm install",
        "pnpm run test",
        "pnpm run build"
    ],
    governance: {
        enforceWorkId: true,
        requiredApprovals: 2, // Strict SOC 2 Two-Reviewer rule
        teamOwner: "FIN" // Financial Core Team
    }
};
// 3. Define a compliant AWS CDK Stack configuration for Cloud Infrastructure
const cdkInfrastructureConfig = {
    stackName: "TransactionifyProductionStack",
    region: "us-east-1",
    accountId: "123456789012",
    environment: "production",
    governance: {
        enforceWorkId: true,
        requiredApprovals: 2,
        teamOwner: "FIN"
    }
};
try {
    console.log("\n🚀 Generating GitHub Workflow Architecture...");
    // We specify target output folders just to keep it contained in this PoC
    const workflowPath = generator.generateGitHubWorkflow(githubProjectConfig, './dist-output/.github/workflows');
    console.log(`[SUCCESS] GitHub Actions workflow created at: ${workflowPath}`);
    console.log("\n🚀 Generating AWS CDK Infrastructure Specification...");
    const cdkPath = generator.generateAwsCdkStack(cdkInfrastructureConfig, './dist-output/infra');
    console.log(`[SUCCESS] AWS CDK CloudFormation manifest created at: ${cdkPath}`);
    console.log("\n✔ [DevEx Platform] All core pipelines successfully generated under compliance rule sets.");
}
catch (error) {
    console.error("❌ Critical error orchestration platform pipelines:", error);
    process.exit(1);
}
