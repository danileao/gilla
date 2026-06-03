import { GitHubWorkflowConfig, AwsCdkConfig } from '../types/index.js';
export declare class DevExGenerator {
    generateGitHubWorkflow(config: GitHubWorkflowConfig, outputDir?: string): string;
    generatePullRequestTemplate(config: Pick<GitHubWorkflowConfig, 'governance'>, outputDir?: string): string;
    private generateSmallTestsJob;
    generateAwsCdkStack(config: AwsCdkConfig, outputDir?: string): string;
    generateAwsCdkStackForEnv(config: AwsCdkConfig, envName?: string, outputDir?: string): string;
}
