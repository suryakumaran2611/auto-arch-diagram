<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph all_AWS[AWS]
  subgraph vpc_aws_vpc_serverless_vpc[VPC
serverless vpc]
    tf_aws_vpc_serverless_vpc["aws_vpc.serverless_vpc"]
    subgraph subnet_aws_subnet_private_subnet[Subnet
private subnet (Private)]
      tf_aws_subnet_private_subnet["aws_subnet.private_subnet"]
      tf_aws_elasticsearch_domain_search_cluster["aws_elasticsearch_domain.search_cluster"]
      tf_aws_lambda_function_data_ingestion["aws_lambda_function.data_ingestion"]
      tf_aws_lambda_function_stream_processor["aws_lambda_function.stream_processor"]
    end
    subgraph subnet_aws_subnet_public_subnet[Subnet
public subnet (Public)]
      tf_aws_subnet_public_subnet["aws_subnet.public_subnet"]
    end
    tf_aws_internet_gateway_igw["aws_internet_gateway.igw"]
    tf_aws_security_group_lambda_sg["aws_security_group.lambda_sg"]
  end
  tf_aws_api_gateway_method_post_data["aws_api_gateway_method.post_data"]
  tf_aws_api_gateway_resource_data_resource["aws_api_gateway_resource.data_resource"]
  tf_aws_api_gateway_rest_api_data_api["aws_api_gateway_rest_api.data_api"]
  tf_aws_athena_workgroup_analytics["aws_athena_workgroup.analytics"]
  tf_aws_cloudwatch_event_rule_scheduled_processing["aws_cloudwatch_event_rule.scheduled_processing"]
  tf_aws_cloudwatch_event_target_lambda_target["aws_cloudwatch_event_target.lambda_target"]
  tf_aws_cloudwatch_log_group_pipeline_logs["aws_cloudwatch_log_group.pipeline_logs"]
  tf_aws_cloudwatch_metric_alarm_lambda_errors["aws_cloudwatch_metric_alarm.lambda_errors"]
  tf_aws_dynamodb_table_metadata["aws_dynamodb_table.metadata"]
  tf_aws_glue_catalog_database_data_catalog["aws_glue_catalog_database.data_catalog"]
  tf_aws_glue_crawler_data_crawler["aws_glue_crawler.data_crawler"]
  tf_aws_iam_role_glue_role["aws_iam_role.glue_role"]
  tf_aws_iam_role_lambda_role["aws_iam_role.lambda_role"]
  tf_aws_iam_role_policy_attachment_glue_service["aws_iam_role_policy_attachment.glue_service"]
  tf_aws_iam_role_policy_attachment_lambda_basic["aws_iam_role_policy_attachment.lambda_basic"]
  tf_aws_iam_role_policy_attachment_lambda_vpc["aws_iam_role_policy_attachment.lambda_vpc"]
  tf_aws_kinesis_stream_data_stream["aws_kinesis_stream.data_stream"]
  tf_aws_lambda_event_source_mapping_dynamodb_to_lambda["aws_lambda_event_source_mapping.dynamodb_to_lambda"]
  tf_aws_lambda_event_source_mapping_kinesis_to_lambda["aws_lambda_event_source_mapping.kinesis_to_lambda"]
  tf_aws_lambda_function_batch_processor["aws_lambda_function.batch_processor"]
  tf_aws_lambda_function_dlq_processor["aws_lambda_function.dlq_processor"]
  tf_aws_lambda_function_dynamodb_stream_handler["aws_lambda_function.dynamodb_stream_handler"]
  tf_aws_lambda_function_s3_event_handler["aws_lambda_function.s3_event_handler"]
  tf_aws_s3_bucket_processed_data["aws_s3_bucket.processed_data"]
  tf_aws_s3_bucket_query_results["aws_s3_bucket.query_results"]
  tf_aws_s3_bucket_raw_data["aws_s3_bucket.raw_data"]
  tf_aws_s3_bucket_notification_bucket_notification["aws_s3_bucket_notification.bucket_notification"]
  tf_aws_sns_topic_alerts["aws_sns_topic.alerts"]
  tf_aws_sns_topic_subscription_email_alerts["aws_sns_topic_subscription.email_alerts"]
  tf_aws_sqs_queue_dlq["aws_sqs_queue.dlq"]
end
tf_aws_api_gateway_resource_data_resource --> tf_aws_api_gateway_method_post_data
tf_aws_api_gateway_rest_api_data_api --> tf_aws_api_gateway_method_post_data
tf_aws_api_gateway_rest_api_data_api --> tf_aws_api_gateway_resource_data_resource
tf_aws_cloudwatch_event_rule_scheduled_processing --> tf_aws_cloudwatch_event_target_lambda_target
tf_aws_dynamodb_table_metadata --> tf_aws_lambda_event_source_mapping_dynamodb_to_lambda
tf_aws_dynamodb_table_metadata --> tf_aws_lambda_function_data_ingestion
tf_aws_elasticsearch_domain_search_cluster --> tf_aws_lambda_function_stream_processor
tf_aws_glue_catalog_database_data_catalog --> tf_aws_glue_crawler_data_crawler
tf_aws_glue_catalog_database_data_catalog --> tf_aws_lambda_function_s3_event_handler
tf_aws_iam_role_glue_role --> tf_aws_glue_crawler_data_crawler
tf_aws_iam_role_glue_role --> tf_aws_iam_role_policy_attachment_glue_service
tf_aws_iam_role_lambda_role --> tf_aws_iam_role_policy_attachment_lambda_basic
tf_aws_iam_role_lambda_role --> tf_aws_iam_role_policy_attachment_lambda_vpc
tf_aws_iam_role_lambda_role --> tf_aws_lambda_function_batch_processor
tf_aws_iam_role_lambda_role --> tf_aws_lambda_function_data_ingestion
tf_aws_iam_role_lambda_role --> tf_aws_lambda_function_dlq_processor
tf_aws_iam_role_lambda_role --> tf_aws_lambda_function_dynamodb_stream_handler
tf_aws_iam_role_lambda_role --> tf_aws_lambda_function_s3_event_handler
tf_aws_iam_role_lambda_role --> tf_aws_lambda_function_stream_processor
tf_aws_kinesis_stream_data_stream --> tf_aws_lambda_event_source_mapping_kinesis_to_lambda
tf_aws_kinesis_stream_data_stream --> tf_aws_lambda_function_data_ingestion
tf_aws_lambda_function_batch_processor --> tf_aws_cloudwatch_event_target_lambda_target
tf_aws_lambda_function_dynamodb_stream_handler --> tf_aws_lambda_event_source_mapping_dynamodb_to_lambda
tf_aws_lambda_function_s3_event_handler --> tf_aws_s3_bucket_notification_bucket_notification
tf_aws_lambda_function_stream_processor --> tf_aws_cloudwatch_metric_alarm_lambda_errors
tf_aws_lambda_function_stream_processor --> tf_aws_lambda_event_source_mapping_kinesis_to_lambda
tf_aws_s3_bucket_processed_data --> tf_aws_glue_crawler_data_crawler
tf_aws_s3_bucket_processed_data --> tf_aws_lambda_function_batch_processor
tf_aws_s3_bucket_processed_data --> tf_aws_lambda_function_stream_processor
tf_aws_s3_bucket_processed_data --> tf_aws_s3_bucket_notification_bucket_notification
tf_aws_s3_bucket_query_results --> tf_aws_athena_workgroup_analytics
tf_aws_s3_bucket_query_results --> tf_aws_lambda_function_s3_event_handler
tf_aws_s3_bucket_raw_data --> tf_aws_lambda_function_batch_processor
tf_aws_s3_bucket_raw_data --> tf_aws_lambda_function_data_ingestion
tf_aws_security_group_lambda_sg --> tf_aws_elasticsearch_domain_search_cluster
tf_aws_security_group_lambda_sg --> tf_aws_lambda_function_data_ingestion
tf_aws_security_group_lambda_sg --> tf_aws_lambda_function_stream_processor
tf_aws_sns_topic_alerts --> tf_aws_cloudwatch_metric_alarm_lambda_errors
tf_aws_sns_topic_alerts --> tf_aws_lambda_function_dlq_processor
tf_aws_sns_topic_alerts --> tf_aws_lambda_function_stream_processor
tf_aws_sns_topic_alerts --> tf_aws_sns_topic_subscription_email_alerts
tf_aws_sqs_queue_dlq --> tf_aws_lambda_function_dlq_processor
tf_aws_subnet_private_subnet --> tf_aws_elasticsearch_domain_search_cluster
tf_aws_subnet_private_subnet --> tf_aws_lambda_function_data_ingestion
tf_aws_subnet_private_subnet --> tf_aws_lambda_function_stream_processor
tf_aws_vpc_serverless_vpc --> tf_aws_internet_gateway_igw
tf_aws_vpc_serverless_vpc --> tf_aws_security_group_lambda_sg
tf_aws_vpc_serverless_vpc --> tf_aws_subnet_private_subnet
tf_aws_vpc_serverless_vpc --> tf_aws_subnet_public_subnet
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact

## AI Architecture Insights

*Reviewed by OpenRouter free vision model `stealth/ox-alpha` (quality score: 3/10).*

**Serverless AWS data pipeline** sharing one `lambda_role`. API Gateway `data_api` POSTs reach `data_ingestion`, which lands raw payloads in `raw_data` and onto Kinesis `data_stream`. `stream_processor` consumes the stream from private subnets, indexing into Elasticsearch `search_cluster` guarded by `lambda_sg`. A scheduled CloudWatch rule runs `batch_processor` across `raw_data` and `processed_data`. Glue `data_crawler` catalogs `processed_data` into `data_catalog`; Athena `analytics` writes query output to `query_results`. DynamoDB `metadata` changes stream to `dynamodb_stream_handler`. Failures collect in SQS `dlq` for `dlq_processor` retries; the `lambda_errors` alarm notifies SNS `alerts`, fanning out to `email_alerts`.

**Context hints**
- `[COMPUTE]` data_ingestion Lambda ingests API POST payloads into raw_data bucket and Kinesis data_stream.
- `[COMPUTE]` stream_processor consumes Kinesis data_stream events; failures raise lambda_errors alarm publishing to alerts.
- `[COMPUTE]` scheduled_processing rule triggers batch_processor over raw_data and processed_data contents.
- `[COMPUTE]` dlq_processor retries failed records from sqs_queue.dlq; alerts fans out to email_alerts.
- `[DATA]` data_crawler catalogs processed_data into data_catalog; Athena analytics stores query output in query_results.
- `[DATA]` dynamodb_stream_handler reacts to metadata table changes via dynamodb_to_lambda event source mapping.

**Contextual labels applied:** `data_api` → Data Ingestion REST API, `data_ingestion` → API Payload Ingester, `raw_data` → Raw Landing Zone, `processed_data` → Curated Data Lake Zone, `query_results` → Athena Query Output Store, `metadata` → Pipeline Metadata Store (+6 more)

**Review notes**
- [layout] Extreme vertical aspect ratio; six stacked clusters force long scrolling and push related nodes thousands of pixels apart.
- [edge-routing] Dozens of blue/red dashed edges span the full canvas height between Network, Security, Other, Compute, Data, Storage; dense crossings converge on the Lambda nodes.
- [labeling] Truncated labels throughout: 'Api Gateway Rest Ap...', 'IAM Role Policy...', 'Cloudwatch Event...', 'Lambda Function dynamodb stream...'.
- [grouping] Security cluster sits mid-canvas far from the six Lambda functions it authorizes; three policy-attachment leaf nodes add noise without information.
- [completeness] public_subnet dangles with no routes or attached resources; several edges encode reverse associations (e.g., search_cluster to stream_processor), obscuring true dependency direction.

Feedback iterations: iter0: 3/10, iter1: 3/10, iter2: 3/10

**AI-refined diagram files** (include legend and review hints): architecture-diagram-ai.png, architecture-diagram-ai.jpg, architecture-diagram-ai.svg
