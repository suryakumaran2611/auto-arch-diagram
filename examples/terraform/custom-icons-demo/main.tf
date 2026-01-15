# Custom Icon Demonstration - Serverless Data Pipeline
# Demonstrates: Custom icon support, serverless architecture, event-driven design

# AWS Provider
provider "aws" {
  region = "us-east-1"
}

# VPC for serverless infrastructure
resource "aws_vpc" "serverless_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name        = "serverless-pipeline-vpc"
    Architecture = "serverless"
  }
}

# Public subnet for API Gateway endpoints
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.serverless_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
  
  tags = {
    Name = "serverless-public-subnet"
    Tier = "public"
  }
}

# Private subnet for Lambda functions
resource "aws_subnet" "private_subnet" {
  vpc_id            = aws_vpc.serverless_vpc.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "us-east-1a"
  
  tags = {
    Name = "serverless-private-subnet"
    Tier = "private"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.serverless_vpc.id
  
  tags = {
    Name = "serverless-igw"
  }
}

# Security Group for Lambda
resource "aws_security_group" "lambda_sg" {
  name        = "serverless-lambda-sg"
  description = "Security group for Lambda functions"
  vpc_id      = aws_vpc.serverless_vpc.id
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "serverless-lambda-sg"
  }
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "data_api" {
  name        = "serverless-data-api"
  description = "API Gateway for serverless data pipeline"
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }
  
  tags = {
    Name = "data-api"
  }
}

resource "aws_api_gateway_resource" "data_resource" {
  rest_api_id = aws_api_gateway_rest_api.data_api.id
  parent_id   = aws_api_gateway_rest_api.data_api.root_resource_id
  path_part   = "data"
}

resource "aws_api_gateway_method" "post_data" {
  rest_api_id   = aws_api_gateway_rest_api.data_api.id
  resource_id   = aws_api_gateway_resource.data_resource.id
  http_method   = "POST"
  authorization = "AWS_IAM"
}

# Lambda function for data ingestion (Custom Icon: DataPipeline)
resource "aws_lambda_function" "data_ingestion" {
  filename         = "lambda_function.zip"
  function_name    = "data-ingestion-pipeline"
  role             = aws_iam_role.lambda_role.arn
  handler          = "ingestion.handler"
  source_code_hash = filebase64sha256("lambda_function.zip")
  runtime          = "python3.11"
  timeout          = 300
  memory_size      = 1024
  
  vpc_config {
    subnet_ids         = [aws_subnet.private_subnet.id]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
  
  environment {
    variables = {
      KINESIS_STREAM = aws_kinesis_stream.data_stream.name
      S3_BUCKET      = aws_s3_bucket.raw_data.id
      DDB_TABLE      = aws_dynamodb_table.metadata.name
    }
  }
  
  tags = {
    Name = "data-ingestion"
    Icon = "custom://datapipeline"  # Custom icon tag
  }
}

# Kinesis Stream for real-time data (Custom Icon: DataStream)
resource "aws_kinesis_stream" "data_stream" {
  name             = "serverless-data-stream"
  shard_count      = 2
  retention_period = 24
  
  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
  
  tags = {
    Name = "data-stream"
    Icon = "custom://datastream"  # Custom icon tag
  }
}

# Lambda function for stream processing (Custom Icon: StreamProcessor)
resource "aws_lambda_function" "stream_processor" {
  filename         = "lambda_function.zip"
  function_name    = "stream-processor"
  role             = aws_iam_role.lambda_role.arn
  handler          = "processor.handler"
  source_code_hash = filebase64sha256("lambda_function.zip")
  runtime          = "python3.11"
  timeout          = 60
  memory_size      = 512
  
  vpc_config {
    subnet_ids         = [aws_subnet.private_subnet.id]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
  
  environment {
    variables = {
      ELASTICSEARCH_ENDPOINT = aws_elasticsearch_domain.search_cluster.endpoint
      S3_PROCESSED_BUCKET    = aws_s3_bucket.processed_data.id
      SNS_TOPIC              = aws_sns_topic.alerts.arn
    }
  }
  
  tags = {
    Name = "stream-processor"
    Icon = "custom://streamprocessor"  # Custom icon tag
  }
}

# Event Source Mapping for Kinesis to Lambda
resource "aws_lambda_event_source_mapping" "kinesis_to_lambda" {
  event_source_arn  = aws_kinesis_stream.data_stream.arn
  function_name     = aws_lambda_function.stream_processor.arn
  starting_position = "LATEST"
  batch_size        = 100
}

# S3 Bucket for raw data
resource "aws_s3_bucket" "raw_data" {
  bucket = "serverless-raw-data-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name = "raw-data-bucket"
  }
}

# S3 Bucket for processed data
resource "aws_s3_bucket" "processed_data" {
  bucket = "serverless-processed-data-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name = "processed-data-bucket"
  }
}

# S3 Event Notification to Lambda (Custom Icon: EventTrigger)
resource "aws_lambda_function" "s3_event_handler" {
  filename         = "lambda_function.zip"
  function_name    = "s3-event-handler"
  role             = aws_iam_role.lambda_role.arn
  handler          = "s3_handler.handler"
  source_code_hash = filebase64sha256("lambda_function.zip")
  runtime          = "python3.11"
  
  environment {
    variables = {
      GLUE_DATABASE = aws_glue_catalog_database.data_catalog.name
      ATHENA_OUTPUT = aws_s3_bucket.query_results.id
    }
  }
  
  tags = {
    Name = "s3-event-handler"
    Icon = "custom://eventtrigger"  # Custom icon tag
  }
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.processed_data.id
  
  lambda_function {
    lambda_function_arn = aws_lambda_function.s3_event_handler.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "processed/"
  }
}

# DynamoDB for metadata tracking
resource "aws_dynamodb_table" "metadata" {
  name           = "serverless-metadata"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "pipeline_id"
  range_key      = "timestamp"
  
  attribute {
    name = "pipeline_id"
    type = "S"
  }
  
  attribute {
    name = "timestamp"
    type = "N"
  }
  
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"
  
  tags = {
    Name = "metadata-table"
  }
}

# DynamoDB Stream to Lambda (Custom Icon: DatabaseStream)
resource "aws_lambda_function" "dynamodb_stream_handler" {
  filename         = "lambda_function.zip"
  function_name    = "dynamodb-stream-handler"
  role             = aws_iam_role.lambda_role.arn
  handler          = "ddb_stream.handler"
  source_code_hash = filebase64sha256("lambda_function.zip")
  runtime          = "python3.11"
  
  tags = {
    Name = "dynamodb-stream-handler"
    Icon = "custom://databasestream"  # Custom icon tag
  }
}

resource "aws_lambda_event_source_mapping" "dynamodb_to_lambda" {
  event_source_arn  = aws_dynamodb_table.metadata.stream_arn
  function_name     = aws_lambda_function.dynamodb_stream_handler.arn
  starting_position = "LATEST"
}

# ElasticSearch for search and analytics (Custom Icon: SearchEngine)
resource "aws_elasticsearch_domain" "search_cluster" {
  domain_name           = "serverless-search"
  elasticsearch_version = "7.10"
  
  cluster_config {
    instance_type  = "t3.small.elasticsearch"
    instance_count = 2
  }
  
  ebs_options {
    ebs_enabled = true
    volume_size = 20
  }
  
  vpc_options {
    subnet_ids         = [aws_subnet.private_subnet.id]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
  
  tags = {
    Name = "search-cluster"
    Icon = "custom://searchengine"  # Custom icon tag
  }
}

# Glue Catalog for data catalog
resource "aws_glue_catalog_database" "data_catalog" {
  name = "serverless_data_catalog"
  
  description = "Data catalog for serverless pipeline"
}

# Glue Crawler (Custom Icon: DataCrawler)
resource "aws_glue_crawler" "data_crawler" {
  database_name = aws_glue_catalog_database.data_catalog.name
  name          = "serverless-data-crawler"
  role          = aws_iam_role.glue_role.arn
  
  s3_target {
    path = "s3://${aws_s3_bucket.processed_data.bucket}/processed/"
  }
  
  tags = {
    Name = "data-crawler"
    Icon = "custom://datacrawler"  # Custom icon tag
  }
}

# Athena Workgroup for queries
resource "aws_athena_workgroup" "analytics" {
  name = "serverless-analytics"
  
  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.query_results.bucket}/results/"
    }
  }
  
  tags = {
    Name = "analytics-workgroup"
  }
}

resource "aws_s3_bucket" "query_results" {
  bucket = "serverless-query-results-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name = "query-results"
  }
}

# EventBridge Rule for scheduled processing (Custom Icon: Scheduler)
resource "aws_cloudwatch_event_rule" "scheduled_processing" {
  name                = "serverless-scheduled-processing"
  description         = "Trigger batch processing every hour"
  schedule_expression = "rate(1 hour)"
  
  tags = {
    Name = "scheduled-processing"
    Icon = "custom://scheduler"  # Custom icon tag
  }
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.scheduled_processing.name
  target_id = "BatchProcessorLambda"
  arn       = aws_lambda_function.batch_processor.arn
}

# Lambda for batch processing
resource "aws_lambda_function" "batch_processor" {
  filename         = "lambda_function.zip"
  function_name    = "batch-processor"
  role             = aws_iam_role.lambda_role.arn
  handler          = "batch.handler"
  source_code_hash = filebase64sha256("lambda_function.zip")
  runtime          = "python3.11"
  timeout          = 900
  memory_size      = 3008
  
  environment {
    variables = {
      S3_INPUT_BUCKET  = aws_s3_bucket.raw_data.id
      S3_OUTPUT_BUCKET = aws_s3_bucket.processed_data.id
    }
  }
  
  tags = {
    Name = "batch-processor"
  }
}

# SNS Topic for alerts (Custom Icon: AlertNotification)
resource "aws_sns_topic" "alerts" {
  name = "serverless-pipeline-alerts"
  
  tags = {
    Name = "pipeline-alerts"
    Icon = "custom://alertnotification"  # Custom icon tag
  }
}

resource "aws_sns_topic_subscription" "email_alerts" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "alerts@example.com"
}

# SQS Queue for dead letter queue (Custom Icon: MessageQueue)
resource "aws_sqs_queue" "dlq" {
  name                      = "serverless-dlq"
  message_retention_seconds = 1209600  # 14 days
  
  tags = {
    Name = "dead-letter-queue"
    Icon = "custom://messagequeue"  # Custom icon tag
  }
}

# Lambda function for DLQ processing
resource "aws_lambda_function" "dlq_processor" {
  filename         = "lambda_function.zip"
  function_name    = "dlq-processor"
  role             = aws_iam_role.lambda_role.arn
  handler          = "dlq.handler"
  source_code_hash = filebase64sha256("lambda_function.zip")
  runtime          = "python3.11"
  
  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }
  
  environment {
    variables = {
      SNS_TOPIC = aws_sns_topic.alerts.arn
    }
  }
  
  tags = {
    Name = "dlq-processor"
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "pipeline_logs" {
  name              = "/aws/serverless/pipeline"
  retention_in_days = 7
  
  tags = {
    Name = "pipeline-logs"
  }
}

# CloudWatch Alarms (Custom Icon: CloudMonitor)
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "serverless-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "Alert when Lambda errors exceed threshold"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    FunctionName = aws_lambda_function.stream_processor.function_name
  }
  
  tags = {
    Name = "lambda-errors-alarm"
    Icon = "custom://cloudmonitor"  # Custom icon tag
  }
}

# IAM Roles
resource "aws_iam_role" "lambda_role" {
  name = "serverless-lambda-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role" "glue_role" {
  name = "serverless-glue-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "glue.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
  role       = aws_iam_role.glue_role.name
}

# Data source
data "aws_caller_identity" "current" {}
