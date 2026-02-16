<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
  subgraph all_AWS[AWS]
    tf_aws_api_gateway_method_post_data["aws_api_gateway_method.post_data"]
    tf_aws_api_gateway_resource_data_resource["aws_api_gateway_resource.data_resource"]
    tf_aws_api_gateway_rest_api_data_api["aws_api_gateway_rest_api.data_api"]
    tf_aws_athena_workgroup_analytics["aws_athena_workgroup.analytics"]
    tf_aws_cloudwatch_event_rule_scheduled_processing["aws_cloudwatch_event_rule.scheduled_processing"]
    tf_aws_cloudwatch_event_target_lambda_target["aws_cloudwatch_event_target.lambda_target"]
    tf_aws_cloudwatch_log_group_pipeline_logs["aws_cloudwatch_log_group.pipeline_logs"]
    tf_aws_cloudwatch_metric_alarm_lambda_errors["aws_cloudwatch_metric_alarm.lambda_errors"]
    tf_aws_dynamodb_table_metadata["aws_dynamodb_table.metadata"]
    tf_aws_elasticsearch_domain_search_cluster["aws_elasticsearch_domain.search_cluster"]
    tf_aws_glue_catalog_database_data_catalog["aws_glue_catalog_database.data_catalog"]
    tf_aws_glue_crawler_data_crawler["aws_glue_crawler.data_crawler"]
    tf_aws_iam_role_glue_role["aws_iam_role.glue_role"]
    tf_aws_iam_role_lambda_role["aws_iam_role.lambda_role"]
    tf_aws_iam_role_policy_attachment_glue_service["aws_iam_role_policy_attachment.glue_service"]
    tf_aws_iam_role_policy_attachment_lambda_basic["aws_iam_role_policy_attachment.lambda_basic"]
    tf_aws_iam_role_policy_attachment_lambda_vpc["aws_iam_role_policy_attachment.lambda_vpc"]
    tf_aws_internet_gateway_igw["aws_internet_gateway.igw"]
    tf_aws_kinesis_stream_data_stream["aws_kinesis_stream.data_stream"]
    tf_aws_lambda_event_source_mapping_dynamodb_to_lambda["aws_lambda_event_source_mapping.dynamodb_to_lambda"]
    tf_aws_lambda_event_source_mapping_kinesis_to_lambda["aws_lambda_event_source_mapping.kinesis_to_lambda"]
    tf_aws_lambda_function_batch_processor["aws_lambda_function.batch_processor"]
    tf_aws_lambda_function_data_ingestion["aws_lambda_function.data_ingestion"]
    tf_aws_lambda_function_dlq_processor["aws_lambda_function.dlq_processor"]
    tf_aws_lambda_function_dynamodb_stream_handler["aws_lambda_function.dynamodb_stream_handler"]
    tf_aws_lambda_function_s3_event_handler["aws_lambda_function.s3_event_handler"]
    tf_aws_lambda_function_stream_processor["aws_lambda_function.stream_processor"]
    tf_aws_s3_bucket_processed_data["aws_s3_bucket.processed_data"]
    tf_aws_s3_bucket_query_results["aws_s3_bucket.query_results"]
    tf_aws_s3_bucket_raw_data["aws_s3_bucket.raw_data"]
    tf_aws_s3_bucket_notification_bucket_notification["aws_s3_bucket_notification.bucket_notification"]
    tf_aws_security_group_lambda_sg["aws_security_group.lambda_sg"]
    tf_aws_sns_topic_alerts["aws_sns_topic.alerts"]
    tf_aws_sns_topic_subscription_email_alerts["aws_sns_topic_subscription.email_alerts"]
    tf_aws_sqs_queue_dlq["aws_sqs_queue.dlq"]
    tf_aws_subnet_private_subnet["aws_subnet.private_subnet"]
    tf_aws_subnet_public_subnet["aws_subnet.public_subnet"]
    tf_aws_vpc_serverless_vpc["aws_vpc.serverless_vpc"]
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
