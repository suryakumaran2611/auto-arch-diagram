output "data_sources_bucket" {
  description = "S3 bucket for data sources"
  value       = aws_s3_bucket.data_sources.id
}

output "raw_data_bucket" {
  description = "S3 bucket for raw data"
  value       = aws_s3_bucket.raw_data.id
}

output "processed_data_bucket" {
  description = "S3 bucket for processed data"
  value       = aws_s3_bucket.processed_data.id
}

output "data_lake_bucket" {
  description = "S3 bucket for data lake"
  value       = aws_s3_bucket.data_lake.id
}

output "ingestion_topic_arn" {
  description = "SNS topic ARN for data ingestion"
  value       = aws_sns_topic.data_ingestion.arn
}

output "processing_queue_url" {
  description = "SQS queue URL for data processing"
  value       = aws_sqs_queue.data_processing_queue.url
}

output "transformation_queue_url" {
  description = "SQS queue URL for data transformation"
  value       = aws_sqs_queue.data_transformation_queue.url
}
