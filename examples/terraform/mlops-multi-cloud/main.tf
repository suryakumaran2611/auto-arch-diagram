# Multi-Cloud MLOps Architecture
# Demonstrates: AWS, Azure, GCP integration with VPCs, cross-cloud networking, distributed ML

# ===== AWS INFRASTRUCTURE =====

# AWS VPC for training infrastructure
resource "aws_vpc" "aws_training_vpc" {
  provider             = aws
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name     = "aws-training-vpc"
    Purpose  = "Model Training"
    Provider = "AWS"
  }
}

# AWS Private Subnet for SageMaker
resource "aws_subnet" "aws_training_subnet" {
  provider          = aws
  vpc_id            = aws_vpc.aws_training_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  
  tags = {
    Name = "aws-training-subnet"
    Tier = "private"
  }
}

# AWS Security Group for SageMaker
resource "aws_security_group" "aws_sagemaker_sg" {
  provider    = aws
  name        = "mlops-sagemaker-sg"
  description = "Security group for SageMaker training"
  vpc_id      = aws_vpc.aws_training_vpc.id
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "mlops-sagemaker-sg"
  }
}

# AWS S3 for training data
resource "aws_s3_bucket" "aws_training_data" {
  provider = aws
  bucket   = "mlops-multicloud-training-data"
  
  tags = {
    Name     = "aws-training-data"
    Purpose  = "Training Data"
    Provider = "AWS"
  }
}

# AWS S3 for model registry
resource "aws_s3_bucket" "aws_model_registry" {
  provider = aws
  bucket   = "mlops-multicloud-model-registry"
  
  tags = {
    Name     = "aws-model-registry"
    Purpose  = "Model Artifacts"
    Provider = "AWS"
  }
}

# AWS SageMaker Training Job
resource "aws_sagemaker_model" "training_model" {
  provider          = aws
  name              = "mlops-multicloud-training-model"
  execution_role_arn = aws_iam_role.sagemaker_role.arn
  
  primary_container {
    image          = "763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-training:2.0-gpu-py310"
    model_data_url = "s3://${aws_s3_bucket.aws_model_registry.id}/models/model.tar.gz"
  }
  
  tags = {
    Name = "mlops-training-model"
  }
}

# AWS DynamoDB for experiment tracking
resource "aws_dynamodb_table" "aws_experiments" {
  provider       = aws
  name           = "mlops-multicloud-experiments"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "experiment_id"
  
  attribute {
    name = "experiment_id"
    type = "S"
  }
  
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"
  
  tags = {
    Name     = "aws-experiments"
    Provider = "AWS"
  }
}

# AWS Lambda for data pipeline
resource "aws_lambda_function" "aws_data_pipeline" {
  provider         = aws
  filename         = "lambda_function.zip"
  function_name    = "mlops-multicloud-data-pipeline"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.handler"
  source_code_hash = filebase64sha256("lambda_function.zip")
  runtime          = "python3.11"
  timeout          = 900
  memory_size      = 3008
  
  vpc_config {
    subnet_ids         = [aws_subnet.aws_training_subnet.id]
    security_group_ids = [aws_security_group.aws_sagemaker_sg.id]
  }
  
  environment {
    variables = {
      S3_BUCKET       = aws_s3_bucket.aws_training_data.id
      DYNAMODB_TABLE  = aws_dynamodb_table.aws_experiments.name
      AZURE_BLOB_URL  = azurerm_storage_account.azure_inference_storage.primary_blob_endpoint
      GCP_BUCKET      = google_storage_bucket.gcp_data_lake.name
    }
  }
  
  tags = {
    Name = "aws-data-pipeline"
  }
}

# AWS Step Functions for orchestration
resource "aws_sfn_state_machine" "aws_ml_orchestrator" {
  provider = aws
  name     = "mlops-multicloud-orchestrator"
  role_arn = aws_iam_role.step_functions_role.arn
  
  definition = jsonencode({
    Comment = "Multi-Cloud ML Pipeline Orchestrator"
    StartAt = "FetchDataFromGCP"
    States = {
      FetchDataFromGCP = {
        Type     = "Task"
        Resource = aws_lambda_function.aws_data_pipeline.arn
        Next     = "TrainOnSageMaker"
      }
      TrainOnSageMaker = {
        Type     = "Task"
        Resource = "arn:aws:states:::sagemaker:createTrainingJob.sync"
        Next     = "DeployToAzure"
      }
      DeployToAzure = {
        Type     = "Task"
        Resource = aws_lambda_function.azure_deployer.arn
        End      = true
      }
    }
  })
  
  tags = {
    Name = "aws-ml-orchestrator"
  }
}

# AWS Lambda for Azure deployment
resource "aws_lambda_function" "azure_deployer" {
  provider         = aws
  filename         = "lambda_function.zip"
  function_name    = "mlops-azure-deployer"
  role             = aws_iam_role.lambda_role.arn
  handler          = "azure_deploy.handler"
  source_code_hash = filebase64sha256("lambda_function.zip")
  runtime          = "python3.11"
  
  environment {
    variables = {
      AZURE_CONTAINER_REGISTRY = azurerm_container_registry.azure_ml_registry.login_server
      MODEL_BUCKET             = aws_s3_bucket.aws_model_registry.id
    }
  }
  
  tags = {
    Name = "azure-deployer"
  }
}

# AWS IAM Roles
resource "aws_iam_role" "sagemaker_role" {
  provider = aws
  name     = "mlops-multicloud-sagemaker-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "sagemaker.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role" "lambda_role" {
  provider = aws
  name     = "mlops-multicloud-lambda-role"
  
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

resource "aws_iam_role" "step_functions_role" {
  provider = aws
  name     = "mlops-multicloud-step-functions-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })
}

# AWS SNS for alerts
resource "aws_sns_topic" "aws_ml_alerts" {
  provider = aws
  name     = "mlops-multicloud-alerts"
  
  tags = {
    Name = "aws-ml-alerts"
  }
}

# AWS CloudWatch for monitoring
resource "aws_cloudwatch_log_group" "aws_ml_logs" {
  provider          = aws
  name              = "/aws/mlops/multicloud"
  retention_in_days = 30
  
  tags = {
    Name = "aws-ml-logs"
  }
}

# ===== AZURE INFRASTRUCTURE =====

# Azure Resource Group
resource "azurerm_resource_group" "azure_mlops" {
  provider = azurerm
  name     = "mlops-multicloud-rg"
  location = "East US"
  
  tags = {
    Purpose  = "Model Inference"
    Provider = "Azure"
  }
}

# Azure Virtual Network
resource "azurerm_virtual_network" "azure_inference_vnet" {
  provider            = azurerm
  name                = "azure-inference-vnet"
  address_space       = ["10.1.0.0/16"]
  location            = azurerm_resource_group.azure_mlops.location
  resource_group_name = azurerm_resource_group.azure_mlops.name
  
  tags = {
    Name     = "azure-inference-vnet"
    Purpose  = "Model Serving"
    Provider = "Azure"
  }
}

# Azure Subnet for AKS
resource "azurerm_subnet" "azure_aks_subnet" {
  provider             = azurerm
  name                 = "azure-aks-subnet"
  resource_group_name  = azurerm_resource_group.azure_mlops.name
  virtual_network_name = azurerm_virtual_network.azure_inference_vnet.name
  address_prefixes     = ["10.1.1.0/24"]
}

# Azure Subnet for Application Gateway
resource "azurerm_subnet" "azure_appgw_subnet" {
  provider             = azurerm
  name                 = "azure-appgw-subnet"
  resource_group_name  = azurerm_resource_group.azure_mlops.name
  virtual_network_name = azurerm_virtual_network.azure_inference_vnet.name
  address_prefixes     = ["10.1.2.0/24"]
}

# Azure Network Security Group
resource "azurerm_network_security_group" "azure_aks_nsg" {
  provider            = azurerm
  name                = "azure-aks-nsg"
  location            = azurerm_resource_group.azure_mlops.location
  resource_group_name = azurerm_resource_group.azure_mlops.name
  
  security_rule {
    name                       = "allow-https"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  
  tags = {
    Name = "azure-aks-nsg"
  }
}

# Azure AKS Cluster for model serving
resource "azurerm_kubernetes_cluster" "azure_ml_cluster" {
  provider            = azurerm
  name                = "azure-ml-cluster"
  location            = azurerm_resource_group.azure_mlops.location
  resource_group_name = azurerm_resource_group.azure_mlops.name
  dns_prefix          = "mlops-multicloud"
  
  default_node_pool {
    name                = "inference"
    node_count          = 3
    vm_size             = "Standard_D8s_v3"
    vnet_subnet_id      = azurerm_subnet.azure_aks_subnet.id
    enable_auto_scaling = true
    min_count           = 2
    max_count           = 10
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  network_profile {
    network_plugin = "azure"
    network_policy = "calico"
  }
  
  tags = {
    Name = "azure-ml-cluster"
  }
}

# Azure Container Registry
resource "azurerm_container_registry" "azure_ml_registry" {
  provider            = azurerm
  name                = "mlopsMulticloudACR"
  resource_group_name = azurerm_resource_group.azure_mlops.name
  location            = azurerm_resource_group.azure_mlops.location
  sku                 = "Premium"
  admin_enabled       = true
  
  georeplications {
    location                = "West US"
    zone_redundancy_enabled = true
  }
  
  tags = {
    Name = "azure-ml-registry"
  }
}

# Azure Storage Account for inference data
resource "azurerm_storage_account" "azure_inference_storage" {
  provider                 = azurerm
  name                     = "mlopsinferstorage"
  resource_group_name      = azurerm_resource_group.azure_mlops.name
  location                 = azurerm_resource_group.azure_mlops.location
  account_tier             = "Standard"
  account_replication_type = "GRS"
  
  blob_properties {
    versioning_enabled = true
  }
  
  tags = {
    Name = "azure-inference-storage"
  }
}

# Azure Cosmos DB for inference logs
resource "azurerm_cosmosdb_account" "azure_inference_logs" {
  provider            = azurerm
  name                = "mlops-multicloud-cosmos"
  location            = azurerm_resource_group.azure_mlops.location
  resource_group_name = azurerm_resource_group.azure_mlops.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  
  consistency_policy {
    consistency_level = "Session"
  }
  
  geo_location {
    location          = azurerm_resource_group.azure_mlops.location
    failover_priority = 0
  }
  
  tags = {
    Name = "azure-inference-logs"
  }
}

# Azure Redis Cache for inference caching
resource "azurerm_redis_cache" "azure_model_cache" {
  provider            = azurerm
  name                = "mlops-multicloud-redis"
  location            = azurerm_resource_group.azure_mlops.location
  resource_group_name = azurerm_resource_group.azure_mlops.name
  capacity            = 2
  family              = "P"
  sku_name            = "Premium"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
  
  redis_configuration {
    maxmemory_policy = "allkeys-lru"
  }
  
  tags = {
    Name = "azure-model-cache"
  }
}

# Azure Application Gateway for load balancing
resource "azurerm_application_gateway" "azure_ml_gateway" {
  provider            = azurerm
  name                = "azure-ml-gateway"
  resource_group_name = azurerm_resource_group.azure_mlops.name
  location            = azurerm_resource_group.azure_mlops.location
  
  sku {
    name     = "WAF_v2"
    tier     = "WAF_v2"
    capacity = 2
  }
  
  gateway_ip_configuration {
    name      = "gateway-ip-config"
    subnet_id = azurerm_subnet.azure_appgw_subnet.id
  }
  
  frontend_port {
    name = "https-port"
    port = 443
  }
  
  frontend_ip_configuration {
    name                 = "frontend-ip"
    public_ip_address_id = azurerm_public_ip.azure_appgw_ip.id
  }
  
  backend_address_pool {
    name = "aks-backend-pool"
  }
  
  backend_http_settings {
    name                  = "http-settings"
    cookie_based_affinity = "Disabled"
    port                  = 80
    protocol              = "Http"
    request_timeout       = 60
  }
  
  http_listener {
    name                           = "https-listener"
    frontend_ip_configuration_name = "frontend-ip"
    frontend_port_name             = "https-port"
    protocol                       = "Https"
    ssl_certificate_name           = "ssl-cert"
  }
  
  ssl_certificate {
    name     = "ssl-cert"
    data     = filebase64("cert.pfx")
    password = "P@ssw0rd123"
  }
  
  request_routing_rule {
    name                       = "routing-rule"
    rule_type                  = "Basic"
    http_listener_name         = "https-listener"
    backend_address_pool_name  = "aks-backend-pool"
    backend_http_settings_name = "http-settings"
    priority                   = 100
  }
  
  tags = {
    Name = "azure-ml-gateway"
  }
}

resource "azurerm_public_ip" "azure_appgw_ip" {
  provider            = azurerm
  name                = "azure-appgw-ip"
  resource_group_name = azurerm_resource_group.azure_mlops.name
  location            = azurerm_resource_group.azure_mlops.location
  allocation_method   = "Static"
  sku                 = "Standard"
  
  tags = {
    Name = "azure-appgw-ip"
  }
}

# Azure Monitor for observability
resource "azurerm_log_analytics_workspace" "azure_monitoring" {
  provider            = azurerm
  name                = "mlops-multicloud-logs"
  location            = azurerm_resource_group.azure_mlops.location
  resource_group_name = azurerm_resource_group.azure_mlops.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  
  tags = {
    Name = "azure-monitoring"
  }
}

# Azure Function for model scoring
resource "azurerm_function_app" "azure_scoring" {
  provider                   = azurerm
  name                       = "mlops-multicloud-scoring"
  location                   = azurerm_resource_group.azure_mlops.location
  resource_group_name        = azurerm_resource_group.azure_mlops.name
  app_service_plan_id        = azurerm_app_service_plan.azure_function_plan.id
  storage_account_name       = azurerm_storage_account.azure_inference_storage.name
  storage_account_access_key = azurerm_storage_account.azure_inference_storage.primary_access_key
  version                    = "~4"
  
  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "MODEL_ENDPOINT"           = azurerm_kubernetes_cluster.azure_ml_cluster.fqdn
    "COSMOS_ENDPOINT"          = azurerm_cosmosdb_account.azure_inference_logs.endpoint
  }
  
  tags = {
    Name = "azure-scoring"
  }
}

resource "azurerm_app_service_plan" "azure_function_plan" {
  provider            = azurerm
  name                = "azure-function-plan"
  location            = azurerm_resource_group.azure_mlops.location
  resource_group_name = azurerm_resource_group.azure_mlops.name
  kind                = "FunctionApp"
  
  sku {
    tier = "ElasticPremium"
    size = "EP1"
  }
}

# ===== GCP INFRASTRUCTURE =====

# GCP VPC for data processing
resource "google_compute_network" "gcp_data_vpc" {
  provider                = google
  name                    = "gcp-data-vpc"
  auto_create_subnetworks = false
  
  description = "GCP VPC for data processing and feature engineering"
}

# GCP Subnet
resource "google_compute_subnetwork" "gcp_data_subnet" {
  provider      = google
  name          = "gcp-data-subnet"
  ip_cidr_range = "10.2.1.0/24"
  region        = "us-central1"
  network       = google_compute_network.gcp_data_vpc.id
  
  private_ip_google_access = true
}

# GCP Firewall Rules
resource "google_compute_firewall" "gcp_allow_internal" {
  provider = google
  name     = "gcp-allow-internal"
  network  = google_compute_network.gcp_data_vpc.name
  
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "icmp"
  }
  
  source_ranges = ["10.2.0.0/16"]
}

# GCP Cloud Storage for data lake
resource "google_storage_bucket" "gcp_data_lake" {
  provider      = google
  name          = "mlops-multicloud-data-lake"
  location      = "US"
  force_destroy = false
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
  
  labels = {
    name     = "gcp-data-lake"
    purpose  = "raw-data"
    provider = "gcp"
  }
}

# GCP BigQuery for feature store
resource "google_bigquery_dataset" "gcp_feature_store" {
  provider                    = google
  dataset_id                  = "mlops_feature_store"
  friendly_name               = "MLOps Feature Store"
  description                 = "Feature store for multi-cloud ML pipelines"
  location                    = "US"
  default_table_expiration_ms = 3600000
  
  labels = {
    name     = "gcp-feature-store"
    provider = "gcp"
  }
}

# GCP BigQuery Table
resource "google_bigquery_table" "gcp_features" {
  provider   = google
  dataset_id = google_bigquery_dataset.gcp_feature_store.dataset_id
  table_id   = "features"
  
  time_partitioning {
    type = "DAY"
  }
  
  schema = jsonencode([
    {
      name = "feature_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "feature_value"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    }
  ])
  
  labels = {
    name = "gcp-features"
  }
}

# GCP Dataflow for data processing
resource "google_dataflow_job" "gcp_data_processor" {
  provider          = google
  name              = "mlops-multicloud-dataflow"
  template_gcs_path = "gs://dataflow-templates/latest/Word_Count"
  temp_gcs_location = "gs://${google_storage_bucket.gcp_data_lake.name}/temp"
  
  parameters = {
    inputFile  = "gs://${google_storage_bucket.gcp_data_lake.name}/input/*"
    output     = "gs://${google_storage_bucket.gcp_data_lake.name}/output/"
  }
  
  network    = google_compute_network.gcp_data_vpc.name
  subnetwork = google_compute_subnetwork.gcp_data_subnet.self_link
  region     = "us-central1"
  
  labels = {
    name = "gcp-data-processor"
  }
}

# GCP Pub/Sub for event streaming
resource "google_pubsub_topic" "gcp_ml_events" {
  provider = google
  name     = "mlops-multicloud-events"
  
  labels = {
    name = "gcp-ml-events"
  }
}

resource "google_pubsub_subscription" "gcp_ml_subscription" {
  provider = google
  name     = "mlops-multicloud-subscription"
  topic    = google_pubsub_topic.gcp_ml_events.name
  
  ack_deadline_seconds = 20
  
  push_config {
    push_endpoint = "https://${aws_lb.aws_ml_endpoint.dns_name}/pubsub/push"
  }
  
  labels = {
    name = "gcp-ml-subscription"
  }
}

# GCP Cloud Functions for data validation
resource "google_cloudfunctions_function" "gcp_data_validator" {
  provider    = google
  name        = "mlops-data-validator"
  description = "Validates incoming data for ML pipeline"
  runtime     = "python311"
  region      = "us-central1"
  
  available_memory_mb   = 2048
  source_archive_bucket = google_storage_bucket.gcp_data_lake.name
  source_archive_object = "functions/validator.zip"
  trigger_http          = true
  entry_point           = "validate_data"
  
  vpc_connector = google_vpc_access_connector.gcp_vpc_connector.name
  
  environment_variables = {
    BIGQUERY_DATASET = google_bigquery_dataset.gcp_feature_store.dataset_id
    PUBSUB_TOPIC     = google_pubsub_topic.gcp_ml_events.name
    AWS_S3_BUCKET    = aws_s3_bucket.aws_training_data.id
  }
  
  labels = {
    name = "gcp-data-validator"
  }
}

resource "google_vpc_access_connector" "gcp_vpc_connector" {
  provider = google
  name     = "gcp-vpc-connector"
  region   = "us-central1"
  network  = google_compute_network.gcp_data_vpc.name
  
  ip_cidr_range = "10.2.100.0/28"
}

# GCP AI Platform for model experimentation
resource "google_notebooks_instance" "gcp_ml_notebook" {
  provider     = google
  name         = "mlops-multicloud-notebook"
  location     = "us-central1-a"
  machine_type = "n1-standard-4"
  
  vm_image {
    project      = "deeplearning-platform-release"
    image_family = "tf2-latest-gpu"
  }
  
  network = google_compute_network.gcp_data_vpc.id
  subnet  = google_compute_subnetwork.gcp_data_subnet.id
  
  labels = {
    name = "gcp-ml-notebook"
  }
}

# GCP Cloud Memorystore (Redis) for caching
resource "google_redis_instance" "gcp_feature_cache" {
  provider           = google
  name               = "mlops-multicloud-redis"
  tier               = "STANDARD_HA"
  memory_size_gb     = 5
  region             = "us-central1"
  
  authorized_network = google_compute_network.gcp_data_vpc.id
  
  redis_version     = "REDIS_7_0"
  display_name      = "MLOps Feature Cache"
  
  labels = {
    name = "gcp-feature-cache"
  }
}

# GCP Cloud Monitoring
resource "google_monitoring_alert_policy" "gcp_ml_alerts" {
  provider     = google
  display_name = "MLOps Multicloud Alerts"
  combiner     = "OR"
  
  conditions {
    display_name = "High Error Rate"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_function\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.1
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.gcp_email.name]
}

resource "google_monitoring_notification_channel" "gcp_email" {
  provider     = google
  display_name = "MLOps Email Alerts"
  type         = "email"
  
  labels = {
    email_address = "mlops-alerts@example.com"
  }
}

# GCP IAM Service Account
resource "google_service_account" "gcp_ml_service_account" {
  provider     = google
  account_id   = "mlops-multicloud-sa"
  display_name = "MLOps Multicloud Service Account"
}

# ===== CROSS-CLOUD NETWORKING =====

# AWS Load Balancer for external access
resource "aws_lb" "aws_ml_endpoint" {
  provider           = aws
  name               = "mlops-multicloud-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.aws_sagemaker_sg.id]
  subnets            = [aws_subnet.aws_training_subnet.id]
  
  tags = {
    Name = "aws-ml-endpoint"
  }
}

# Provider configurations
provider "aws" {
  region = "us-east-1"
}

provider "azurerm" {
  features {}
}

provider "google" {
  project = "mlops-multicloud"
  region  = "us-central1"
}
