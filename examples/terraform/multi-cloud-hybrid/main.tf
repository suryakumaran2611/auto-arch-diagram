terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
}

# ============================================
# AWS COMPONENTS
# ============================================

# S3 Data Lake
resource "aws_s3_bucket" "data_lake" {
  bucket = "multi-cloud-data-lake-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "multi-cloud-data-lake"
  }
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Lambda for Data Processing
resource "aws_iam_role" "lambda_role" {
  name = "multi-cloud-lambda-role"

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
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3" {
  name = "lambda-s3-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject"
      ]
      Resource = "${aws_s3_bucket.data_lake.arn}/*"
    }]
  })
}

resource "aws_lambda_function" "data_processor" {
  filename      = "lambda_placeholder.zip"
  function_name = "multi-cloud-data-processor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"

  environment {
    variables = {
      DATA_LAKE_BUCKET = aws_s3_bucket.data_lake.id
    }
  }

  tags = {
    Name = "data-processor"
  }
}

# SNS Topic
resource "aws_sns_topic" "data_events" {
  name = "multi-cloud-data-events"

  tags = {
    Name = "data-events-topic"
  }
}

# RDS PostgreSQL
resource "aws_db_subnet_group" "main" {
  name            = "multi-cloud-db-subnet"
  subnets         = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "multi-cloud-db-subnet"
  }
}

resource "aws_security_group" "rds" {
  name        = "multi-cloud-rds-sg"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "multi-cloud-rds-sg"
  }
}

resource "aws_db_instance" "postgres" {
  identifier            = "multi-cloud-postgres"
  engine                = "postgres"
  engine_version        = "15.3"
  instance_class        = "db.t3.small"
  allocated_storage     = 20
  username              = var.db_username
  password              = var.db_password
  db_subnet_group_name  = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible   = false
  skip_final_snapshot   = true

  tags = {
    Name = "multi-cloud-postgres"
  }
}

# VPC for AWS
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name = "multi-cloud-vpc"
  }
}

resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "multi-cloud-private-1"
  }
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name = "multi-cloud-private-2"
  }
}

# ============================================
# GCP COMPONENTS
# ============================================

# GCS Bucket
resource "google_storage_bucket" "data_warehouse" {
  name          = "multi-cloud-data-warehouse-${data.google_client_config.current.project}"
  location      = var.gcp_region
  force_destroy = false

  labels = {
    name = "data-warehouse"
  }
}

# BigQuery Dataset
resource "google_bigquery_dataset" "analytics" {
  dataset_id    = "multi_cloud_analytics"
  friendly_name = "Multi Cloud Analytics"
  location      = var.gcp_region

  labels = {
    name = "analytics"
  }
}

# Cloud Function
resource "google_storage_bucket" "functions" {
  name     = "multi-cloud-cloud-functions-${data.google_client_config.current.project}"
  location = var.gcp_region
}

resource "google_cloudfunctions_function" "analytics_processor" {
  name        = "multi-cloud-analytics-processor"
  description = "Process analytics data"
  runtime     = "python39"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.functions.name
  source_archive_object = "function.zip"

  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = google_storage_bucket.data_warehouse.name
  }

  entry_point = "process_data"

  labels = {
    name = "analytics-processor"
  }
}

# Cloud SQL PostgreSQL
resource "google_sql_database_instance" "postgres" {
  name             = "multi-cloud-postgres"
  database_version = "POSTGRES_15"
  region           = var.gcp_region

  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"
    }
  }

  labels = {
    name = "postgres"
  }
}

resource "google_sql_database" "app_db" {
  name     = "app_database"
  instance = google_sql_database_instance.postgres.name
}

# Pub/Sub Topic and Subscription
resource "google_pubsub_topic" "events" {
  name = "multi-cloud-events"

  labels = {
    name = "events"
  }
}

resource "google_pubsub_subscription" "events_sub" {
  name    = "multi-cloud-events-sub"
  topic   = google_pubsub_topic.events.name

  push_config {
    push_endpoint = google_cloudfunctions_function.analytics_processor.https_trigger_url
  }

  labels = {
    name = "events-subscription"
  }
}

# ============================================
# AZURE COMPONENTS
# ============================================

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "multi-cloud-rg"
  location = var.azure_location
}

# Storage Account (Data Lake)
resource "azurerm_storage_account" "datalake" {
  name                     = "multicloudlake${replace(data.azurerm_client_config.current.subscription_id, "-", "")}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "GRS"

  tags = {
    name = "datalake"
  }
}

resource "azurerm_storage_container" "processed" {
  name                  = "processed-data"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}

# Azure SQL Database
resource "azurerm_mssql_server" "main" {
  name                         = "multi-cloud-sqlserver"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = "12.0"
  administrator_login          = var.sql_admin_username
  administrator_login_password = var.sql_admin_password

  tags = {
    name = "sqlserver"
  }
}

resource "azurerm_mssql_database" "app_db" {
  name           = "app_database"
  server_id      = azurerm_mssql_server.main.id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  license_type   = "LicenseIncluded"
  sku_name       = "S0"

  tags = {
    name = "app-database"
  }
}

# Cosmos DB
resource "azurerm_cosmosdb_account" "main" {
  name                = "multi-cloud-cosmosdb"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  tags = {
    name = "cosmosdb"
  }
}

resource "azurerm_cosmosdb_sql_database" "app_db" {
  account_name            = azurerm_cosmosdb_account.main.name
  resource_group_name     = azurerm_resource_group.main.name
  name                    = "app_database"
}

# Azure Function App
resource "azurerm_service_plan" "main" {
  name                = "multi-cloud-service-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "Y1"

  tags = {
    name = "service-plan"
  }
}

resource "azurerm_linux_function_app" "data_processor" {
  name                = "multi-cloud-data-processor"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  storage_account_name       = azurerm_storage_account.datalake.name
  storage_account_access_key = azurerm_storage_account.datalake.primary_access_key

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    STORAGE_ACCOUNT_NAME = azurerm_storage_account.datalake.name
  }

  tags = {
    name = "data-processor"
  }
}

# Event Grid Topic
resource "azurerm_eventgrid_topic" "events" {
  name                = "multi-cloud-events"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = {
    name = "events"
  }
}

# Event Grid Subscription
resource "azurerm_eventgrid_event_subscription" "data_processor" {
  name              = "data-processor-subscription"
  scope             = azurerm_eventgrid_topic.events.id
  event_delivery_schema = "EventGridSchema"

  webhook_endpoint {
    url = azurerm_linux_function_app.data_processor.default_hostname
  }

  tags = {
    name = "subscription"
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "google_client_config" "current" {}
data "azurerm_client_config" "current" {}
