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

# DynamoDB Tables
resource "aws_dynamodb_table" "orders" {
  name           = "orders"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "order_id"
  stream_specification {
    stream_view_type = "NEW_AND_OLD_IMAGES"
    stream_enabled   = true
  }

  attribute {
    name = "order_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  global_secondary_index {
    name            = "user_id-timestamp-index"
    hash_key        = "user_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expiration_date"
    enabled        = true
  }

  tags = {
    Name = "orders-table"
  }
}

resource "aws_dynamodb_table" "payments" {
  name           = "payments"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "payment_id"
  stream_specification {
    stream_view_type = "NEW_AND_OLD_IMAGES"
    stream_enabled   = true
  }

  attribute {
    name = "payment_id"
    type = "S"
  }

  attribute {
    name = "order_id"
    type = "S"
  }

  global_secondary_index {
    name            = "order_id-index"
    hash_key        = "order_id"
    projection_type = "ALL"
  }

  tags = {
    Name = "payments-table"
  }
}

resource "aws_dynamodb_table" "notifications" {
  name           = "notifications"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "notification_id"

  attribute {
    name = "notification_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  global_secondary_index {
    name            = "user_id-index"
    hash_key        = "user_id"
    projection_type = "ALL"
  }

  tags = {
    Name = "notifications-table"
  }
}

# SNS Topics
resource "aws_sns_topic" "order_events" {
  name = "order-events"

  tags = {
    Name = "order-events-topic"
  }
}

resource "aws_sns_topic" "payment_events" {
  name = "payment-events"

  tags = {
    Name = "payment-events-topic"
  }
}

resource "aws_sns_topic" "notification_events" {
  name = "notification-events"

  tags = {
    Name = "notification-events-topic"
  }
}

resource "aws_sns_topic" "email_notifications" {
  name = "email-notifications"

  tags = {
    Name = "email-notifications-topic"
  }
}

# SQS Queues
resource "aws_sqs_queue" "order_dlq" {
  name                      = "order-processing-dlq"
  message_retention_seconds = 1209600

  tags = {
    Name = "order-processing-dlq"
  }
}

resource "aws_sqs_queue" "order_queue" {
  name                       = "order-processing-queue"
  message_retention_seconds  = 345600
  visibility_timeout_seconds = 120

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.order_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "order-processing-queue"
  }
}

resource "aws_sqs_queue" "payment_dlq" {
  name                      = "payment-processing-dlq"
  message_retention_seconds = 1209600

  tags = {
    Name = "payment-processing-dlq"
  }
}

resource "aws_sqs_queue" "payment_queue" {
  name                       = "payment-processing-queue"
  message_retention_seconds  = 345600
  visibility_timeout_seconds = 180

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.payment_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "payment-processing-queue"
  }
}

# SNS to SQS Subscriptions
resource "aws_sns_topic_subscription" "order_to_queue" {
  topic_arn = aws_sns_topic.order_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.order_queue.arn

  raw_message_delivery = true
}

resource "aws_sns_topic_subscription" "payment_to_queue" {
  topic_arn = aws_sns_topic.payment_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.payment_queue.arn

  raw_message_delivery = true
}

# SQS Queue Policies
resource "aws_sqs_queue_policy" "order_queue" {
  queue_url = aws_sqs_queue.order_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "sns.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.order_queue.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_sns_topic.order_events.arn
        }
      }
    }]
  })
}

resource "aws_sqs_queue_policy" "payment_queue" {
  queue_url = aws_sqs_queue.payment_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "sns.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.payment_queue.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_sns_topic.payment_events.arn
        }
      }
    }]
  })
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "serverless-events-lambda-role"

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

resource "aws_iam_role_policy" "lambda_dynamodb_access" {
  name = "lambda-dynamodb-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.orders.arn,
          aws_dynamodb_table.payments.arn,
          aws_dynamodb_table.notifications.arn,
          "${aws_dynamodb_table.orders.arn}/index/*",
          "${aws_dynamodb_table.payments.arn}/index/*",
          "${aws_dynamodb_table.notifications.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:DescribeStream",
          "dynamodb:ListStreams",
          "dynamodb:ListTables"
        ]
        Resource = [
          aws_dynamodb_table.orders.arn,
          aws_dynamodb_table.payments.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          aws_sns_topic.order_events.arn,
          aws_sns_topic.payment_events.arn,
          aws_sns_topic.notification_events.arn,
          aws_sns_topic.email_notifications.arn
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
          aws_sqs_queue.order_queue.arn,
          aws_sqs_queue.payment_queue.arn
        ]
      }
    ]
  })
}

# Lambda Functions
resource "aws_lambda_function" "api_handler" {
  filename      = "lambda_placeholder.zip"
  function_name = "serverless-api-handler"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 30

  environment {
    variables = {
      ORDERS_TABLE   = aws_dynamodb_table.orders.name
      SNS_TOPIC_ARN  = aws_sns_topic.order_events.arn
    }
  }

  tags = {
    Name = "api-handler"
  }
}

resource "aws_lambda_function" "order_processor" {
  filename      = "lambda_placeholder.zip"
  function_name = "order-processor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 60

  environment {
    variables = {
      ORDERS_TABLE       = aws_dynamodb_table.orders.name
      PAYMENTS_TOPIC_ARN = aws_sns_topic.payment_events.arn
    }
  }

  tags = {
    Name = "order-processor"
  }
}

resource "aws_lambda_function" "payment_processor" {
  filename      = "lambda_placeholder.zip"
  function_name = "payment-processor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 90

  environment {
    variables = {
      PAYMENTS_TABLE      = aws_dynamodb_table.payments.name
      NOTIFICATIONS_TOPIC = aws_sns_topic.notification_events.arn
    }
  }

  tags = {
    Name = "payment-processor"
  }
}

resource "aws_lambda_function" "notification_sender" {
  filename      = "lambda_placeholder.zip"
  function_name = "notification-sender"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 60

  environment {
    variables = {
      NOTIFICATIONS_TABLE = aws_dynamodb_table.notifications.name
      EMAIL_TOPIC_ARN     = aws_sns_topic.email_notifications.arn
    }
  }

  tags = {
    Name = "notification-sender"
  }
}

# Event Source Mappings
resource "aws_lambda_event_source_mapping" "order_processor_mapping" {
  event_source_arn  = aws_sqs_queue.order_queue.arn
  function_name     = aws_lambda_function.order_processor.function_name
  batch_size        = 10
  function_response_types = ["ReportBatchItemFailures"]

  depends_on = [aws_iam_role_policy.lambda_dynamodb_access]
}

resource "aws_lambda_event_source_mapping" "payment_processor_mapping" {
  event_source_arn  = aws_sqs_queue.payment_queue.arn
  function_name     = aws_lambda_function.payment_processor.function_name
  batch_size        = 5
  function_response_types = ["ReportBatchItemFailures"]

  depends_on = [aws_iam_role_policy.lambda_dynamodb_access]
}

resource "aws_lambda_event_source_mapping" "notification_sender_mapping" {
  event_source_arn = aws_dynamodb_table.payments.stream_arn
  function_name    = aws_lambda_function.notification_sender.function_name
  batch_size       = 100
  starting_position = "LATEST"

  depends_on = [aws_iam_role_policy.lambda_dynamodb_access]
}

# API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "serverless-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers = ["Content-Type"]
    allow_methods = ["GET", "POST", "PUT", "DELETE"]
    allow_origins = ["*"]
  }

  tags = {
    Name = "serverless-api"
  }
}

resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "prod"
  auto_deploy = true

  tags = {
    Name = "serverless-api-prod"
  }
}

resource "aws_apigatewayv2_integration" "api_handler" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  integration_method = "POST"
  integration_uri    = aws_lambda_function.api_handler.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "api_handler" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /orders"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/serverless-api"
  retention_in_days = 14

  tags = {
    Name = "serverless-api-logs"
  }
}

# Data source
data "aws_caller_identity" "current" {}
