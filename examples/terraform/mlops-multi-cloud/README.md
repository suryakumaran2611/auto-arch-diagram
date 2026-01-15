# MLOps Multi-Cloud Architecture

⚠️ **Work in Progress** - This example is currently under development due to HCL2 parser compatibility issues with multi-provider configurations.

## Planned Features

This example will demonstrate:
- **Multi-Cloud Integration**: AWS (training) + Azure (inference) + GCP (data)
- **AWS**: SageMaker training, S3 model registry, Step Functions orchestration
- **Azure**: AKS cluster for serving, Container Registry, Cosmos DB logging
- **GCP**: BigQuery feature store, Dataflow processing, Cloud Functions validation
- **Cross-Cloud**: AWS SNS → GCP Pub/Sub, Azure → AWS model deployment
- **Professional Styling**: Provider-specific colors, cross-cloud dotted lines

## Current Status

The Terraform configuration exists but diagram generation is pending parser improvements for:
- Multi-provider blocks (`provider "aws"`, `provider "azurerm"`, `provider "google"`)
- Complex cross-references between providers
- `filebase64sha256()` and `jsonencode()` functions in resource attributes

## Alternative

See [../custom-icons-demo/](../custom-icons-demo/) for a working complex example with 40+ resources demonstrating:
- Event-driven architecture
- Multiple data stores
- Custom icons
- Professional styling

## Architecture Overview

```
GCP (Data Layer)
└── BigQuery Feature Store ← Cloud Functions (validation)
└── Cloud Storage Data Lake ← Dataflow (processing)
└── Pub/Sub Events

       ↓ (data flow)

AWS (Training Layer)
└── SageMaker Training ← Step Functions (orchestration)
└── S3 Model Registry ← Lambda (preprocessing)
└── DynamoDB Experiments

       ↓ (model artifacts)

Azure (Inference Layer)
└── AKS Cluster (serving) ← Container Registry
└── Cosmos DB (logs) ← Redis Cache
└── Application Gateway (LB)
```

## Resources Planned (70+ total)

### AWS (20 resources)
VPC, Subnets, SageMaker, S3, Lambda, Step Functions, DynamoDB, SNS, CloudWatch

### Azure (25 resources)
Virtual Network, Subnets, AKS, Container Registry, Storage Account, Cosmos DB, Redis Cache, Application Gateway, Log Analytics, Functions

### GCP (25 resources)
VPC, Subnets, BigQuery, Cloud Storage, Dataflow, Pub/Sub, Cloud Functions, Notebooks, Redis, Monitoring

Check back in a future release for full diagram support!
