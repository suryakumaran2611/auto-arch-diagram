output "api_endpoint" {
  description = "API Gateway endpoint"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "orders_table_name" {
  description = "Orders DynamoDB table name"
  value       = aws_dynamodb_table.orders.name
}

output "payments_table_name" {
  description = "Payments DynamoDB table name"
  value       = aws_dynamodb_table.payments.name
}

output "notifications_table_name" {
  description = "Notifications DynamoDB table name"
  value       = aws_dynamodb_table.notifications.name
}

output "order_events_topic_arn" {
  description = "Order events SNS topic ARN"
  value       = aws_sns_topic.order_events.arn
}

output "payment_events_topic_arn" {
  description = "Payment events SNS topic ARN"
  value       = aws_sns_topic.payment_events.arn
}
