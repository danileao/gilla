export type TargetEnvironment = 'development' | 'staging' | 'production';
export interface GovernanceConfig {
    enforceWorkId: boolean;
    requiredApprovals: number;
    teamOwner: string;
}
export interface EnvironmentConfig {
    accountId: string;
    region: string;
}
export interface TestStages {
    unit: string;
    pbt?: string;
    contract?: string;
}
export interface GitHubWorkflowConfig {
    name: string;
    environment: TargetEnvironment;
    buildSteps: string[];
    governance: GovernanceConfig;
    environments?: Record<string, EnvironmentConfig>;
    cliSource?: string;
    testStages?: TestStages;
    aiReview?: boolean;
}
export interface AwsCdkConfig {
    stackName: string;
    region: string;
    accountId: string;
    environment: TargetEnvironment;
    governance: GovernanceConfig;
}
