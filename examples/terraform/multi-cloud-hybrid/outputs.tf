output "aws_data_lake_bucket" {
  description = "AWS S3 data lake bucket"
  value       = aws_s3_bucket.data_lake.id
}

output "aws_rds_endpoint" {
  description = "AWS RDS endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "gcp_storage_bucket" {
  description = "GCP Cloud Storage bucket"
  value       = google_storage_bucket.data_warehouse.name
}

output "gcp_bigquery_dataset" {
  description = "GCP BigQuery dataset"
  value       = google_bigquery_dataset.analytics.dataset_id
}

output "gcp_cloudsql_endpoint" {
  description = "GCP Cloud SQL endpoint"
  value       = google_sql_database_instance.postgres.connection_name
}

output "azure_storage_account" {
  description = "Azure Storage Account name"
  value       = azurerm_storage_account.datalake.name
}

output "azure_sql_server" {
  description = "Azure SQL Server FQDN"
  value       = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "azure_cosmosdb_endpoint" {
  description = "Azure Cosmos DB endpoint"
  value       = azurerm_cosmosdb_account.main.endpoint
}
