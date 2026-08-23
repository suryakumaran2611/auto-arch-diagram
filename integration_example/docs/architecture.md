<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph all_AWS[AWS]
  subgraph vpc_aws_vpc_ml_vpc[VPC
ml vpc]
    tf_aws_vpc_ml_vpc["aws_vpc.ml_vpc"]
    subgraph subnet_aws_subnet_private_a[Subnet
private a (Private)]
      tf_aws_subnet_private_a["aws_subnet.private_a"]
      tf_aws_elasticache_cluster_online["aws_elasticache_cluster.online"]
      tf_aws_lambda_function_preprocess["aws_lambda_function.preprocess"]
      tf_aws_rds_cluster_features["aws_rds_cluster.features"]
      tf_aws_sagemaker_notebook_instance_notebook["aws_sagemaker_notebook_instance.notebook"]
    end
    subgraph subnet_aws_subnet_private_b[Subnet
private b (Private)]
      tf_aws_subnet_private_b["aws_subnet.private_b"]
    end
    subgraph subnet_aws_subnet_public_a[Subnet
public a (Public)]
      tf_aws_subnet_public_a["aws_subnet.public_a"]
      tf_aws_nat_gateway_nat["aws_nat_gateway.nat"]
    end
    subgraph subnet_aws_subnet_public_b[Subnet
public b (Public)]
      tf_aws_subnet_public_b["aws_subnet.public_b"]
    end
    tf_aws_db_subnet_group_aurora["aws_db_subnet_group.aurora"]
    tf_aws_elasticache_subnet_group_cache["aws_elasticache_subnet_group.cache"]
    tf_aws_network_acl_private_nacl["aws_network_acl.private_nacl"]
    tf_aws_sagemaker_domain_ml["aws_sagemaker_domain.ml"]
    tf_aws_security_group_eks_sg["aws_security_group.eks_sg"]
  end
  tf_aws_cloudwatch_event_rule_nightly["aws_cloudwatch_event_rule.nightly"]
  tf_aws_cloudwatch_event_target_nightly["aws_cloudwatch_event_target.nightly"]
  tf_aws_cloudwatch_log_group_pipeline_logs["aws_cloudwatch_log_group.pipeline_logs"]
  tf_aws_cloudwatch_log_metric_filter_training_failed["aws_cloudwatch_log_metric_filter.training_failed"]
  tf_aws_cloudwatch_metric_alarm_error_rate["aws_cloudwatch_metric_alarm.error_rate"]
  tf_aws_cloudwatch_metric_alarm_latency["aws_cloudwatch_metric_alarm.latency"]
  tf_aws_dynamodb_table_experiments["aws_dynamodb_table.experiments"]
  tf_aws_ecr_repository_trainer["aws_ecr_repository.trainer"]
  tf_aws_eip_nat["aws_eip.nat"]
  subgraph cluster_aws_eks_cluster_ml[EKS Cluster
ml]
    tf_aws_eks_cluster_ml["aws_eks_cluster.ml"]
    tf_aws_eks_node_group_gpu["aws_eks_node_group.gpu"]
  end
  tf_aws_glue_catalog_database_lake["aws_glue_catalog_database.lake"]
  tf_aws_glue_crawler_raw["aws_glue_crawler.raw"]
  tf_aws_glue_job_feature_job["aws_glue_job.feature_job"]
  tf_aws_iam_role_eks_cluster_role["aws_iam_role.eks_cluster_role"]
  tf_aws_iam_role_eks_node_role["aws_iam_role.eks_node_role"]
  tf_aws_iam_role_events_role["aws_iam_role.events_role"]
  tf_aws_iam_role_glue_role["aws_iam_role.glue_role"]
  tf_aws_iam_role_lambda_role["aws_iam_role.lambda_role"]
  tf_aws_iam_role_sagemaker_role["aws_iam_role.sagemaker_role"]
  tf_aws_iam_role_sfn_role["aws_iam_role.sfn_role"]
  tf_aws_iam_role_policy_attachment_eks_cluster["aws_iam_role_policy_attachment.eks_cluster"]
  tf_aws_iam_role_policy_attachment_eks_cni["aws_iam_role_policy_attachment.eks_cni"]
  tf_aws_iam_role_policy_attachment_eks_registry["aws_iam_role_policy_attachment.eks_registry"]
  tf_aws_iam_role_policy_attachment_eks_worker["aws_iam_role_policy_attachment.eks_worker"]
  tf_aws_internet_gateway_igw["aws_internet_gateway.igw"]
  tf_aws_kinesis_stream_ingest["aws_kinesis_stream.ingest"]
  tf_aws_kms_key_main["aws_kms_key.main"]
  tf_aws_lambda_event_source_mapping_kinesis["aws_lambda_event_source_mapping.kinesis"]
  tf_aws_lambda_function_remediator["aws_lambda_function.remediator"]
  tf_aws_lambda_permission_sns["aws_lambda_permission.sns"]
  tf_aws_s3_bucket_curated["aws_s3_bucket.curated"]
  tf_aws_s3_bucket_models["aws_s3_bucket.models"]
  tf_aws_s3_bucket_processed["aws_s3_bucket.processed"]
  tf_aws_s3_bucket_raw["aws_s3_bucket.raw"]
  tf_aws_s3_bucket_versioning_models["aws_s3_bucket_versioning.models"]
  tf_aws_sagemaker_endpoint_ep["aws_sagemaker_endpoint.ep"]
  tf_aws_sagemaker_endpoint_configuration_ep_config["aws_sagemaker_endpoint_configuration.ep_config"]
  tf_aws_sagemaker_feature_group_store["aws_sagemaker_feature_group.store"]
  tf_aws_sagemaker_model_model["aws_sagemaker_model.model"]
  tf_aws_security_group_rds_sg["aws_security_group.rds_sg"]
  tf_aws_security_group_sagemaker_sg["aws_security_group.sagemaker_sg"]
  tf_aws_sfn_state_machine_pipeline["aws_sfn_state_machine.pipeline"]
  tf_aws_sns_topic_alerts["aws_sns_topic.alerts"]
  tf_aws_sns_topic_subscription_alerts_email["aws_sns_topic_subscription.alerts_email"]
  tf_aws_sns_topic_subscription_alerts_lambda["aws_sns_topic_subscription.alerts_lambda"]
  tf_aws_sqs_queue_dlq["aws_sqs_queue.dlq"]
end
tf_aws_cloudwatch_event_rule_nightly --> tf_aws_cloudwatch_event_target_nightly
tf_aws_db_subnet_group_aurora --> tf_aws_rds_cluster_features
tf_aws_eip_nat --> tf_aws_nat_gateway_nat
tf_aws_eks_cluster_ml --> tf_aws_eks_node_group_gpu
tf_aws_elasticache_subnet_group_cache --> tf_aws_elasticache_cluster_online
tf_aws_glue_catalog_database_lake --> tf_aws_glue_crawler_raw
tf_aws_iam_role_eks_cluster_role --> tf_aws_eks_cluster_ml
tf_aws_iam_role_eks_cluster_role --> tf_aws_iam_role_policy_attachment_eks_cluster
tf_aws_iam_role_events_role --> tf_aws_cloudwatch_event_target_nightly
tf_aws_iam_role_lambda_role --> tf_aws_lambda_function_preprocess
tf_aws_internet_gateway_igw --> tf_aws_nat_gateway_nat
tf_aws_kinesis_stream_ingest --> tf_aws_lambda_event_source_mapping_kinesis
tf_aws_lambda_function_preprocess --> tf_aws_lambda_event_source_mapping_kinesis
tf_aws_lambda_function_preprocess --> tf_aws_sfn_state_machine_pipeline
tf_aws_lambda_function_remediator --> tf_aws_lambda_permission_sns
tf_aws_s3_bucket_models --> tf_aws_s3_bucket_versioning_models
tf_aws_s3_bucket_processed --> tf_aws_lambda_function_preprocess
tf_aws_s3_bucket_processed --> tf_aws_sagemaker_feature_group_store
tf_aws_s3_bucket_raw --> tf_aws_lambda_function_preprocess
tf_aws_sns_topic_alerts --> tf_aws_lambda_function_remediator
tf_aws_sns_topic_alerts --> tf_aws_lambda_permission_sns
tf_aws_subnet_private_a --> tf_aws_db_subnet_group_aurora
tf_aws_subnet_private_a --> tf_aws_lambda_function_preprocess
tf_aws_subnet_private_a --> tf_aws_sagemaker_domain_ml
tf_aws_subnet_private_a --> tf_aws_sagemaker_notebook_instance_notebook
tf_aws_subnet_private_b --> tf_aws_db_subnet_group_aurora
tf_aws_vpc_ml_vpc --> tf_aws_security_group_eks_sg
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact

## AI Architecture Insights

*Reviewed by OpenRouter free vision model `stealth/ox-alpha` (quality score: 4/10).*

**Architecture.** Medallion-lake MLOps platform on AWS: an EventBridge nightly schedule drives a Step Functions pipeline coordinating Glue ETL, SageMaker training, and endpoint deployment; Kinesis->Lambda streaming preprocessing feeds the same orchestrator.
**Dataflow.** 1) Scheduled trigger; 2) Kinesis events preprocessed; 3) raw S3 -> Glue feature job; 4) processed S3 -> Feature Store; 5) ECR image -> model -> endpoint config -> live endpoint.
**Security.** One KMS CMK across buckets, RDS, and SageMaker; per-service IAM roles; private subnets with NAT egress, NACL, and chained SGs (eks->rds); versioned model bucket; SQS DLQ.
**Scaling.** GPU EKS nodes for training, shard-scalable Kinesis, serverless Lambda/Glue, Aurora multi-AZ; CloudWatch error-rate and latency alarms drive SNS alerts and Lambda auto-remediation.

**Context hints**
- `[KMS]` Single KMS key encrypts S3, RDS, and SageMaker artifacts centrally
- `[S3]` Medallion layout: raw, processed, curated buckets; models bucket versioned for rollback
- `[IAM]` Dedicated IAM role per service enforces least-privilege pipeline execution
- `[NETWORK]` Workloads in private subnets; NAT egress; NACL plus layered security groups
- `[DATA]` Kinesis ingest, Glue ETL, and Step Functions orchestrate nightly retraining
- `[COMPUTE]` GPU EKS nodes handle training; SageMaker serves real-time inference

**Contextual labels applied:** `kinesis_stream.ingest` → Streaming Ingestion Entry, `lambda_function.preprocess` → Preprocess Lambda, `sfn_state_machine.pipeline` → Pipeline Orchestrator, `glue_job.feature_job` → Feature Engineering Job, `sagemaker_endpoint.ep` → Model Inference Endpoint, `sagemaker_feature_group.store` → Online Feature Store (+6 more)

**Review notes**
- [layout] Extreme vertical aspect ratio with vast empty canvas; content compressed into left and right columns
- [grouping] 'Other' group is a catch-all mixing monitoring, ML, messaging, and orchestration resources
- [edge-routing] Red dashed security edges traverse the full canvas height, crossing groups and data-flow edges
- [labeling] Multiple node labels truncated (Cloudwatch Log..., Sagemaker Notebook..., Elasticache Subnet...)
- [edge-routing] Blue data-flow edges overlap near Lambda preprocess and Step Functions, obscuring direction

Feedback iterations: iter0: 4/10, iter1: 3/10, iter2: 4/10

**AI-refined diagram files** (include legend and review hints): architecture-ai.png, architecture-ai.jpg, architecture-ai.svg, architecture-ai.html, architecture-ai.drawio
