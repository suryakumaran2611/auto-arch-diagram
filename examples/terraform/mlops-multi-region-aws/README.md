# MLOps Multi-Region AWS Architecture

Enterprise MLOps pipeline with multi-region disaster recovery across us-east-1 (primary) and us-west-2 (DR) with 46 resources.

![Architecture Diagram](architecture-diagram.png)

## Features

- **Multi-Region Architecture**: Primary (us-east-1) + DR (us-west-2)
- **VPC Peering**: Cross-region connectivity
- **EKS Cluster**: Kubernetes for ML workloads with GPU nodes
- **Feature Store**: RDS Aurora + ElastiCache Redis
- **Data Lake**: S3 buckets for training data, models, and raw data
- **ML Pipeline**: Step Functions orchestrating SageMaker + Lambda
- **Experiment Tracking**: DynamoDB with global secondary indexes
- **Security**: Security groups, NACLs, KMS encryption
- **Monitoring**: CloudWatch, SNS alerts

## Resources (46 total)

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

## Generate Diagram

```bash
python tools/generate_arch_diagram.py \
  --iac-root examples/terraform/mlops-multi-region-aws \
  --out-png examples/terraform/mlops-multi-region-aws/architecture-diagram.png
```
