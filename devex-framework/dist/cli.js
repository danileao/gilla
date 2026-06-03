#!/usr/bin/env node
"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const fs = __importStar(require("node:fs"));
const path = __importStar(require("node:path"));
const generator_js_1 = require("./core/generator.js");
const generator = new generator_js_1.DevExGenerator();
const configPath = path.join(process.cwd(), 'devex.json');
console.log("==> [DevEx Framework] Executing Automated Pipeline Generation...");
if (!fs.existsSync(configPath)) {
    console.error("❌ Error: 'devex.json' configuration file not found in the root directory.");
    console.log("💡 Hint: Create a 'devex.json' file specifying your teamOwner and buildSteps.");
    process.exit(1);
}
try {
    const rawData = fs.readFileSync(configPath, 'utf-8');
    const projectConfig = JSON.parse(rawData);
    console.log("🚀 Generating GitHub Workflow...");
    const workflowPath = generator.generateGitHubWorkflow(projectConfig, '.github/workflows');
    console.log(`[SUCCESS] GitHub Actions workflow created at: ${workflowPath}`);
    console.log("🚀 Generating Standardized PR Template...");
    const prTemplatePath = generator.generatePullRequestTemplate(projectConfig, '.github');
    console.log(`[SUCCESS] PR template created at: ${prTemplatePath}`);
    if (projectConfig.environments) {
        console.log("🚀 Generating per-environment CDK stacks...");
        for (const [envName, envConfig] of Object.entries(projectConfig.environments)) {
            const cdkConfig = {
                stackName: `${projectConfig.name.replace(/\s+/g, '')}${envName.charAt(0).toUpperCase() + envName.slice(1)}Stack`,
                region: envConfig.region,
                accountId: envConfig.accountId,
                environment: projectConfig.environment,
                governance: projectConfig.governance,
            };
            const cdkPath = generator.generateAwsCdkStackForEnv(cdkConfig, envName, 'infra');
            console.log(`  [SUCCESS] CDK stack for '${envName}' created at: ${cdkPath}`);
        }
    }
    else {
        console.log("🚀 Generating default AWS CDK Infrastructure Tags...");
        const cdkConfig = {
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
}
catch (error) {
    console.error("❌ Critical error during automated generation:", error);
    process.exit(1);
}
