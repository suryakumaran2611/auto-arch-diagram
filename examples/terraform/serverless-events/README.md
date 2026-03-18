# Serverless Events Platform (AWS)

This example demonstrates an event-driven serverless backend with asynchronous processing.

## What It Includes

- API Gateway HTTP API for order ingestion
- Multiple Lambda functions for orchestration and processing
- SNS topics for event fan-out
- SQS queues with dead-letter queues
- DynamoDB tables with indexes and streams
- IAM roles and policies for service-to-service access
- CloudWatch log group for observability

## Files

- `main.tf`: Event-driven architecture resources
- `variables.tf`: Deployment region
- `outputs.tf`: API endpoint and data/topic identifiers

## Generate Diagram

```bash
python tools/generate_arch_diagram.py --changed-files examples/terraform/serverless-events/main.tf --direction AUTO --out-md examples/terraform/serverless-events/architecture-diagram.md --out-mmd examples/terraform/serverless-events/architecture-diagram.mmd
```