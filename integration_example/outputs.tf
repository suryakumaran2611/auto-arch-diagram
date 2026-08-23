output "sagemaker_endpoint" {
  description = "SageMaker real-time endpoint name"
  value       = aws_sagemaker_endpoint.ep.name
}

output "pipeline_arn" {
  description = "Step Functions pipeline ARN"
  value       = aws_sfn_state_machine.pipeline.arn
}

output "data_lake_buckets" {
  description = "S3 data lake buckets"
  value = {
    raw       = aws_s3_bucket.raw.bucket
    processed = aws_s3_bucket.processed.bucket
    curated   = aws_s3_bucket.curated.bucket
    models    = aws_s3_bucket.models.bucket
  }
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.ml_vpc.id
}

output "alerts_topic" {
  description = "SNS alerts topic ARN"
  value       = aws_sns_topic.alerts.arn
}
