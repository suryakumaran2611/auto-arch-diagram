# Simple Multi-Cloud Demo

Basic multi-cloud infrastructure spanning AWS, Azure, and GCP with 7 core resources demonstrating cross-cloud storage patterns.

![Architecture Diagram](architecture-diagram.png)

## Features

- **Multi-Cloud Storage**: S3 (AWS), Blob Storage (Azure), Cloud Storage (GCP)
- **Simple Networking**: Basic VPC and subnet setup
- **Cross-Cloud Data Sharing**: Shared storage buckets/containers across providers
- **Production Ready**: Proper tagging, security configurations, and naming conventions
- **Easy to Deploy**: Minimal dependencies and configuration required

## Architecture Overview

```
Multi-Cloud Storage Architecture (Network Segregation)
├── AWS Network (aws-network)
│   ├── VPC (10.0.0.0/16) - vpc_aws_network
│   └── Subnet (10.0.1.0/24) - subnet_aws_network
│
├── Global Network (global)
│   ├── S3 Bucket - s3_global (AWS)
│   ├── Storage Account - storage_global (Azure)
│   ├── Storage Container - container_global (Azure)
│   └── Cloud Storage Bucket - bucket_global (GCP)
│
└── Azure Network (azure-network)
    └── Resource Group - rg_azure_network (contains Azure resources)
```

**Network Information**: Each component label shows its network context (e.g., "vpc aws network", "s3 global") to clearly indicate network segregation across the multi-cloud setup.
Multi-Cloud Storage Architecture
├── AWS Region
│   ├── VPC (10.0.0.0/16)
│   ├── Subnet (10.0.1.0/24)
│   └── S3 Bucket (multi-cloud-demo-shared-data)
│
├── Azure Region
│   ├── Resource Group (multi-cloud-demo-rg)
│   ├── Storage Account (multicloudstorage)
│   └── Storage Container (shared-data)
│
└── GCP Region
    └── Cloud Storage Bucket (multi-cloud-demo-shared-data)
```

## Resources (7 total) - Network Segregation

### AWS Network (aws-network) - 2 resources
- **VPC** (10.0.0.0/16): Virtual network for AWS resources
- **Subnet** (10.0.1.0/24): Private subnet within VPC

### Global Network (global) - 4 resources
- **S3 Bucket** (AWS): Globally accessible storage for cross-cloud data sharing
- **Storage Account** (Azure): Globally accessible blob storage
- **Storage Container** (Azure): Private container within storage account
- **Cloud Storage Bucket** (GCP): Globally accessible object storage

### Azure Network (azure-network) - 1 resource
- **Resource Group**: Logical container for Azure resources in East US region

## Prerequisites

Before deploying, configure your cloud providers:

### AWS
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Azure
```bash
az login
export ARM_SUBSCRIPTION_ID="your-subscription-id"
```

### GCP
```bash
gcloud auth login
export GOOGLE_PROJECT="your-project-id"
```

## Deploy

```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply changes
terraform apply
```

## Generate Diagram

```bash
python tools/generate_arch_diagram.py \
  --changed-files examples/terraform/mlops-multi-cloud/main.tf \
  --out-png examples/terraform/mlops-multi-cloud/architecture-diagram.png
```

## Use Cases

This simple multi-cloud setup is ideal for:

- **Cross-cloud data sharing** and backup strategies
- **Multi-cloud storage architectures**
- **Learning multi-cloud patterns** without complexity
- **Testing cloud provider integrations**
- **Basic multi-cloud networking** demonstrations

## Extending the Example

To make this more production-ready, you could add:

- **Load balancers** and **CDNs** for each cloud
- **Cross-cloud networking** (VPNs, peering)
- **Monitoring and logging** across providers
- **Security policies** and access controls
- **CI/CD pipelines** for multi-cloud deployments
