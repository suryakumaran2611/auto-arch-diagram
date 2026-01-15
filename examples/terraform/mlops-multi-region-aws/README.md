# MLOps Multi-Region AWS Architecture

⚠️ **Work in Progress** - This example is currently under development due to HCL2 parser compatibility issues with multi-region provider aliases.

## Planned Features

This example will demonstrate:
- **Multi-Region Architecture**: Primary (us-east-1) + DR (us-west-2)
- **VPC Peering**: Cross-region connectivity
- **EKS Cluster**: Kubernetes for ML workloads with GPU nodes
- **Feature Store**: RDS Aurora + ElastiCache Redis
- **Data Lake**: S3 buckets for training data, models, and raw data
- **ML Pipeline**: Step Functions orchestrating SageMaker + Lambda
- **Experiment Tracking**: DynamoDB with global secondary indexes
- **Security**: Security groups, NACLs, KMS encryption
- **Monitoring**: CloudWatch, SNS alerts

## Current Status

The Terraform configuration exists but diagram generation is pending parser improvements for:
- Provider aliases (`provider = aws.us-west-2`)
- Complex `jsonencode()` expressions
- Multi-region VPC peering

## Alternative

See [../custom-icons-demo/](../custom-icons-demo/) for a working complex example with 40+ resources demonstrating all tool capabilities.

## Resources Planned (46 total)

- VPCs (2), Subnets (4), Internet Gateway, NAT Gateway, VPC Peering
- Security Groups (3), Network ACL
- EKS Cluster + Node Group  
- Application Load Balancer
- RDS Aurora Cluster + Read Replica
- ElastiCache Redis
- S3 Buckets (3)
- DynamoDB Table
- Lambda Functions (3)
- Step Functions State Machine
- SageMaker Notebook
- SNS Topic, CloudWatch Log Group, KMS Key
- IAM Roles (5)

Check back in a future release for full diagram support!
