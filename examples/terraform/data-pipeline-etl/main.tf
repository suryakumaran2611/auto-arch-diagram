terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# S3 Buckets for Data Pipeline
resource "aws_s3_bucket" "data_sources" {
  bucket = "data-sources-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "data-sources"
  }
}

resource "aws_s3_bucket" "raw_data" {
  bucket = "raw-data-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "raw-data"
  }
}

resource "aws_s3_bucket" "processed_data" {
  bucket = "processed-data-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "processed-data"
  }
}

resource "aws_s3_bucket" "data_lake" {
  bucket = "data-lake-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "data-lake"
  }
}

resource "aws_s3_bucket_versioning" "all" {
  for_each = toset([
    aws_s3_bucket.data_sources.id,
    aws_s3_bucket.raw_data.id,
    aws_s3_bucket.processed_data.id,
    aws_s3_bucket.data_lake.id,
  ])

  bucket = each.value

  versioning_configuration {
    status = "Enabled"
  }
}

# SNS Topics
resource "aws_sns_topic" "data_ingestion" {
  name = "data-ingestion-topic"

  tags = {
    Name = "data-ingestion-topic"
  }
}

resource "aws_sns_topic" "processing_events" {
  name = "processing-events-topic"

  tags = {
    Name = "processing-events-topic"
  }
}

resource "aws_sns_topic" "transformation_events" {
  name = "transformation-events-topic"

  tags = {
    Name = "transformation-events-topic"
  }
}

# SQS Queues
resource "aws_sqs_queue" "data_ingestion_dlq" {
  name                      = "data-ingestion-dlq"
  message_retention_seconds = 1209600

  tags = {
    Name = "data-ingestion-dlq"
  }
}

resource "aws_sqs_queue" "data_processing_queue" {
  name                       = "data-processing-queue"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.data_ingestion_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "data-processing-queue"
  }
}

resource "aws_sqs_queue" "data_transformation_queue" {
  name                       = "data-transformation-queue"
  visibility_timeout_seconds = 600
  message_retention_seconds  = 1209600

  tags = {
    Name = "data-transformation-queue"
  }
}

# SNS to SQS subscriptions
resource "aws_sns_topic_subscription" "processing_to_queue" {
  topic_arn = aws_sns_topic.processing_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.data_processing_queue.arn

  raw_message_delivery = true
}

resource "aws_sns_topic_subscription" "transformation_to_queue" {
  topic_arn = aws_sns_topic.transformation_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.data_transformation_queue.arn

  raw_message_delivery = true
}

# SQS Queue Policies
resource "aws_sqs_queue_policy" "data_processing" {
  queue_url = aws_sqs_queue.data_processing_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "sns.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.data_processing_queue.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_sns_topic.processing_events.arn
        }
      }
    }]
  })
}

resource "aws_sqs_queue_policy" "data_transformation" {
  queue_url = aws_sqs_queue.data_transformation_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "sns.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.data_transformation_queue.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_sns_topic.transformation_events.arn
        }
      }
    }]
  })
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "data-pipeline-lambda-role"

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

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3_access" {
  name = "lambda-s3-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_sources.arn,
          "${aws_s3_bucket.data_sources.arn}/*",
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.processed_data.arn}/*",
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          aws_sns_topic.processing_events.arn,
          aws_sns_topic.transformation_events.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.data_processing_queue.arn,
          aws_sqs_queue.data_transformation_queue.arn
        ]
      }
    ]
  })
}

# Lambda Functions
resource "aws_lambda_function" "data_ingestion" {
  filename      = "lambda_placeholder.zip"
  function_name = "data-ingestion-function"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 60

  environment {
    variables = {
      RAW_DATA_BUCKET = aws_s3_bucket.raw_data.id
      SNS_TOPIC_ARN   = aws_sns_topic.processing_events.arn
    }
  }

  tags = {
    Name = "data-ingestion-function"
  }
}

resource "aws_lambda_function" "data_processing" {
  filename      = "lambda_placeholder.zip"
  function_name = "data-processing-function"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 300

  environment {
    variables = {
      PROCESSED_DATA_BUCKET = aws_s3_bucket.processed_data.id
      SNS_TOPIC_ARN         = aws_sns_topic.transformation_events.arn
    }
  }

  tags = {
    Name = "data-processing-function"
  }
}

resource "aws_lambda_function" "data_transformation" {
  filename      = "lambda_placeholder.zip"
  function_name = "data-transformation-function"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 300

  environment {
    variables = {
      DATA_LAKE_BUCKET = aws_s3_bucket.data_lake.id
    }
  }

  tags = {
    Name = "data-transformation-function"
  }
}

# SQS Event Source Mapping
resource "aws_lambda_event_source_mapping" "data_processing" {
  event_source_arn = aws_sqs_queue.data_processing_queue.arn
  function_name    = aws_lambda_function.data_processing.function_name
  batch_size       = 10

  depends_on = [aws_iam_role_policy.lambda_s3_access]
}

resource "aws_lambda_event_source_mapping" "data_transformation" {
  event_source_arn = aws_sqs_queue.data_transformation_queue.arn
  function_name    = aws_lambda_function.data_transformation.function_name
  batch_size       = 5

  depends_on = [aws_iam_role_policy.lambda_s3_access]
}

# EventBridge Rules for Scheduling
resource "aws_cloudwatch_event_rule" "data_ingestion_schedule" {
  name                = "data-ingestion-schedule"
  description         = "Trigger data ingestion every hour"
  schedule_expression = "rate(1 hour)"

  tags = {
    Name = "data-ingestion-schedule"
  }
}

resource "aws_cloudwatch_event_target" "data_ingestion" {
  rule      = aws_cloudwatch_event_rule.data_ingestion_schedule.name
  target_id = "DataIngestionLambda"
  arn       = aws_lambda_function.data_ingestion.arn

  role_arn = aws_iam_role.eventbridge_role.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_ingestion.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.data_ingestion_schedule.arn
}

# IAM Role for EventBridge
resource "aws_iam_role" "eventbridge_role" {
  name = "eventbridge-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_lambda_invoke" {
  name = "eventbridge-lambda-invoke"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "lambda:InvokeFunction"
      ]
      Resource = [
        aws_lambda_function.data_ingestion.arn
      ]
    }]
  })
}

# AWS Glue Catalog Database
resource "aws_glue_catalog_database" "data_pipeline" {
  name = "data_pipeline"

  description = "Data Pipeline Glue Catalog"
}

# AWS Glue Job
resource "aws_iam_role" "glue_role" {
  name = "glue-pipeline-role"

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

resource "aws_iam_role_policy_attachment" "glue_service_role" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3_access" {
  name = "glue-s3-access"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*",
          aws_s3_bucket.processed_data.arn,
          "${aws_s3_bucket.processed_data.arn}/*",
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_glue_job" "etl_job" {
  name     = "data-pipeline-etl-job"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.data_sources.id}/glue-scripts/etl.py"
  }

  default_arguments = {
    "--job-bookmark-option" = "job-bookmark-enable"
  }

  glue_version = "4.0"
  max_retries  = 1
  max_capacity = 10

  tags = {
    Name = "data-pipeline-etl-job"
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/data-pipeline"
  retention_in_days = 14

  tags = {
    Name = "data-pipeline-lambda-logs"
  }
}

resource "aws_cloudwatch_log_group" "glue_logs" {
  name              = "/aws/glue/data-pipeline"
  retention_in_days = 30

  tags = {
    Name = "data-pipeline-glue-logs"
  }
}

# Data source
data "aws_caller_identity" "current" {}
