# Multi-Tier Web App (AWS)

This example models a production-style three-tier web application in AWS.

## What It Includes

- VPC with public and private subnets across two AZs
- Internet gateway and route table associations
- Application Load Balancer and target group
- Auto Scaling Group with launch template
- RDS PostgreSQL for relational data
- ElastiCache Redis for caching
- S3 bucket for static assets
- CloudFront distribution in front of web delivery

## Files

- `main.tf`: Core infrastructure resources
- `variables.tf`: Configurable parameters (region, sizing, DB settings)
- `outputs.tf`: Endpoints and key resource identifiers

## Generate Diagram

```bash
python tools/generate_arch_diagram.py --changed-files examples/terraform/multi-tier-web-app/main.tf --direction AUTO --out-md examples/terraform/multi-tier-web-app/architecture-diagram.md --out-mmd examples/terraform/multi-tier-web-app/architecture-diagram.mmd
```