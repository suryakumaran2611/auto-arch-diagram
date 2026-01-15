// Secure serverless website (AWS CDK) - reference skeleton.
// Note: the generator currently doesn't statically parse CDK programs.
// This example exists as a security-focused starting point for CDK users.
//
// Recommended controls:
// - S3 bucket private + OAC, CloudFront, TLS, WAF
// - Access logs and versioning
// - Least-privilege IAM

import * as cdk from 'aws-cdk-lib';

export class ServerlessWebsiteStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Intentionally minimal: see README for Terraform/CloudFormation working examples.
  }
}

const app = new cdk.App();
new ServerlessWebsiteStack(app, 'AutoArchServerlessWebsite');
