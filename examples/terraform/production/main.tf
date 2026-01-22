# ------------------------------------------------------------------------
# Production Multi-Cloud Infrastructure
# Complex enterprise architecture with TerraVision integration testing
# Demonstrates multi-provider setup, advanced networking, security, and monitoring
# ------------------------------------------------------------------------

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # ------------------------------------------------------------------------
  # PROVIDERS CONFIGURATION
  # ------------------------------------------------------------------------
  
  # AWS Provider - Production East Coast
  provider "aws" {
    region = var.aws_region
    alias = "prod_east"
    
    default_tags {
      Environment     = "production"
      Project        = "multi-cloud-platform"
      ManagedBy      = "terraform"
      CostCenter     = "engineering"
      Compliance     = "sox"
    }
  }
  
  # Azure Provider - Production Central US
  provider "azurerm" {
    features {}
    alias = "prod_central"
    
    default_tags {
      Environment = "production"
      Project    = "multi-cloud-platform"
      ManagedBy  = "terraform"
    }
  }
  
  # Google Cloud Provider - Production Central US
  provider "google" {
    region = var.gcp_region
    project = var.gcp_project_id
    alias = "prod_central"
    
    default_tags {
      Environment = "production"
      Project    = "multi-cloud-platform"
      ManagedBy  = "terraform"
    }
  }
  
  # Random Provider for unique naming
  provider "random" {
    # Keep default for production use
  }
}

# ------------------------------------------------------------------------
# VARIABLES
# ------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS region for production resources"
  type        = string
  default     = "us-east-1"
  
  validation {
    condition     = can(regex("^us-[a-z]+-[1-3]", var.aws_region))
    error_message = "The AWS region must be a valid US region (e.g., us-east-1)."
  }
}

variable "gcp_region" {
  description = "GCP region for production resources"
  type        = string
  default     = "us-central1"
  
  validation {
    condition     = can(regex("^us-[a-z]+-[1-9]", var.gcp_region))
    error_message = "The GCP region must be a valid US region (e.g., us-central1)."
  }
}

variable "gcp_project_id" {
  description = "GCP project ID for production resources"
  type        = string
  default     = "multi-cloud-prod"
  
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]+", var.gcp_project_id))
    error_message = "The GCP project ID must be a valid project identifier."
  }
}

variable "azure_location" {
  description = "Azure region for production resources"
  type        = string
  default     = "East US"
  
  validation {
    condition     = contains(["East US", "West US", "Central US"], var.azure_location)
    error_message = "The Azure location must be one of: East US, West US, Central US."
  }
}

variable "environment" {
  description = "Environment name for resource tagging"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Base name for resources"
  type        = string
  default     = "multi-cloud"
}

variable "enable_monitoring" {
  description = "Enable comprehensive monitoring and logging"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Enable backup and disaster recovery"
  type        = bool
  default     = true
}

variable "enable_security" {
  description = "Enable advanced security features"
  type        = bool
  default     = true
}

# ------------------------------------------------------------------------
# LOCAL VALUES
# ------------------------------------------------------------------------

locals {
  # Common naming convention
  name_prefix = "${var.project_name}-${var.environment}"
  
  # Tag sets for consistent labeling
  common_tags = merge(
    {
      Name        = "${local.name_prefix}"
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    },
    var.enable_monitoring ? {
      Monitoring = "enabled"
      Backup     = var.enable_backup ? "enabled" : "disabled"
      Security   = var.enable_security ? "enhanced" : "standard"
    } : {}
  )
  
  # CIDR blocks for networking
  vpc_cidr = {
    aws   = "10.0.0.0/16"
    azure = "10.1.0.0/16"
    gcp   = "10.2.0.0/16"
  }
}

# ------------------------------------------------------------------------
# DATA SOURCES
# ------------------------------------------------------------------------

# Random ID for unique resource naming
resource "random_id" "this" {
  keepers = {
    # Change this to force recreation of resources
    timestamp = timestamp()
  }
}

# AWS KMS Key for encryption
data "aws_kms_key" "main" {
  key_id = "alias/multi-cloud-platform-kms"
}

# Azure Key Vault for secrets
data "azurerm_key_vault" "main" {
  name                = "${local.name_prefix}-kv"
  resource_group_name = "${local.name_prefix}-rg"
}

# GCP KMS Key for encryption
data "google_kms_crypto_key" "main" {
  key_id = "multi-cloud-platform-key"
}

# ------------------------------------------------------------------------
# NETWORKING LAYER
# ------------------------------------------------------------------------

module "aws_networking" {
  source = "../../modules/aws-networking"
  
  providers = {
    aws = aws.prod_east
  }
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  vpc_cidr = local.vpc_cidr.aws
  
  enable_dns_hostnames    = true
  enable_flow_logs      = var.enable_monitoring
  enable_vpc_flow_logs  = var.enable_monitoring
  
  tags = local.common_tags
}

module "azure_networking" {
  source = "../../modules/azure-networking"
  
  providers = {
    azurerm = azurerm.prod_central
  }
  
  name_prefix = local.name_prefix
  location    = var.azure_location
  
  vnet_address_space = [local.vpc_cidr.azure]
  
  enable_dns          = true
  enable_monitoring    = var.enable_monitoring
  
  tags = local.common_tags
}

module "gcp_networking" {
  source = "../../modules/gcp-networking"
  
  providers = {
    google = google.prod_central
  }
  
  name_prefix = local.name_prefix
  project_id  = var.gcp_project_id
  
  network_name = "${local.name_prefix}-vpc"
  auto_create_subnetworks = true
  
  vpc_cidr    = local.vpc_cidr.gcp
  
  enable_logging = var.enable_monitoring
  
  tags = local.common_tags
}

# ------------------------------------------------------------------------
# SECURITY LAYER
# ------------------------------------------------------------------------

module "aws_security" {
  source = "../../modules/aws-security"
  
  providers = {
    aws = aws.prod_east
  }
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  vpc_id = module.aws_networking.vpc_id
  
  enable_security_hub = var.enable_security
  enable_guardduty     = var.enable_monitoring
  enable_macie        = var.enable_security
  
  kms_key_id = data.aws_kms_key.main.arn
  
  tags = local.common_tags
}

module "azure_security" {
  source = "../../modules/azure-security"
  
  providers = {
    azurerm = azurerm.prod_central
  }
  
  name_prefix = local.name_prefix
  location    = var.azure_location
  
  vnet_id = module.azure_networking.vnet_id
  
  enable_security_center = var.enable_security
  enable_monitoring       = var.enable_monitoring
  
  key_vault_id = data.azurerm_key_vault.main.id
  
  tags = local.common_tags
}

module "gcp_security" {
  source = "../../modules/gcp-security"
  
  providers = {
    google = google.prod_central
  }
  
  name_prefix = local.name_prefix
  project_id  = var.gcp_project_id
  
  network_name = module.gcp_networking.network_name
  
  enable_security_command_center = var.enable_security
  enable_cloud_armor       = var.enable_security
  enable_monitoring           = var.enable_monitoring
  
  kms_key_id = data.google_kms_crypto_key.main.id
  
  tags = local.common_tags
}

# ------------------------------------------------------------------------
# COMPUTE LAYER
# ------------------------------------------------------------------------

module "aws_compute" {
  source = "../../modules/aws-compute"
  
  providers = {
    aws = aws.prod_east
  }
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  vpc_id              = module.aws_networking.vpc_id
  public_subnet_ids    = module.aws_networking.public_subnet_ids
  private_subnet_ids   = module.aws_networking.private_subnet_ids
  
  instance_type        = "m5.large"
  key_pair_name       = "${local.name_prefix}-key"
  
  enable_monitoring    = var.enable_monitoring
  enable_autoscaling  = true
  
  min_capacity         = 2
  max_capacity         = 10
  desired_capacity     = 4
  
  tags = local.common_tags
}

module "azure_compute" {
  source = "../../modules/azure-compute"
  
  providers = {
    azurerm = azurerm.prod_central
  }
  
  name_prefix = local.name_prefix
  location    = var.azure_location
  
  resource_group_name = module.azure_networking.resource_group_name
  vnet_id            = module.azure_networking.vnet_id
  subnet_ids          = module.azure_networking.subnet_ids
  
  vm_size       = "Standard_D2s_v3"
  admin_username = "${local.name_prefix}-admin"
  
  enable_monitoring = var.enable_monitoring
  enable_backup     = var.enable_backup
  
  instance_count  = 3
  
  tags = local.common_tags
}

module "gcp_compute" {
  source = "../../modules/gcp-compute"
  
  providers = {
    google = google.prod_central
  }
  
  name_prefix = local.name_prefix
  project_id  = var.gcp_project_id
  
  network_name = module.gcp_networking.network_name
  region       = var.gcp_region
  
  machine_type = "e2-standard-2"
  image_family = "ubuntu-2004-lts"
  
  enable_monitoring = var.enable_monitoring
  enable_backup     = var.enable_backup
  
  instance_count = 2
  
  tags = local.common_tags
}

# ------------------------------------------------------------------------
# DATABASE LAYER
# ------------------------------------------------------------------------

module "aws_database" {
  source = "../../modules/aws-database"
  
  providers = {
    aws = aws.prod_east
  }
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  vpc_id             = module.aws_networking.vpc_id
  private_subnet_ids  = module.aws_networking.private_subnet_ids
  
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = "db.r5.large"
  
  allocated_storage = 100
  max_allocated_storage = 1000
  
  enable_monitoring = var.enable_monitoring
  enable_backup     = var.enable_backup
  enable_encryption = var.enable_security
  
  kms_key_id      = data.aws_kms_key.main.arn
  
  database_name    = "${local.name_prefix}-postgres"
  username         = "${local.name_prefix}_admin"
  
  tags = local.common_tags
}

module "azure_database" {
  source = "../../modules/azure-database"
  
  providers = {
    azurerm = azurerm.prod_central
  }
  
  name_prefix = local.name_prefix
  location    = var.azure_location
  
  resource_group_name = module.azure_networking.resource_group_name
  vnet_id            = module.azure_networking.vnet_id
  subnet_id          = module.azure_networking.database_subnet_ids
  
  engine    = "PostgreSQL"
  version   = "14"
  
  sku_name = "GP_Gen5_2"
  
  enable_monitoring = var.enable_monitoring
  enable_backup     = var.enable_backup
  enable_encryption = var.enable_security
  
  key_vault_id = data.azurerm_key_vault.main.id
  
  database_name = "${local.name_prefix}-postgres"
  administrator_login = "${local.name_prefix}_admin"
  
  tags = local.common_tags
}

module "gcp_database" {
  source = "../../modules/gcp-database"
  
  providers = {
    google = google.prod_central
  }
  
  name_prefix = local.name_prefix
  project_id  = var.gcp_project_id
  
  region = var.gcp_region
  
  database_version = "POSTGRES_14"
  tier        = "db-n1-standard-2"
  
  enable_monitoring = var.enable_monitoring
  enable_backup     = var.enable_backup
  enable_encryption = var.enable_security
  
  kms_key_name = "${local.name_prefix}-db-key"
  
  database_name = "${local.name_prefix}-postgres"
  
  tags = local.common_tags
}

# ------------------------------------------------------------------------
# STORAGE LAYER
# ------------------------------------------------------------------------

module "aws_storage" {
  source = "../../modules/aws-storage"
  
  providers = {
    aws = aws.prod_east
  }
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  enable_versioning  = true
  enable_encryption  = var.enable_security
  
  buckets = {
    "${local.name_prefix}-app-data" = {
      versioning_enabled = true
      lifecycle_enabled = true
    },
    "${local.name_prefix}-backups" = {
      versioning_enabled = true
      lifecycle_enabled = true
    },
    "${local.name_prefix}-logs" = {
      versioning_enabled = false
      lifecycle_enabled = true
    }
  }
  
  kms_key_id = data.aws_kms_key.main.arn
  
  tags = local.common_tags
}

module "azure_storage" {
  source = "../../modules/azure-storage"
  
  providers = {
    azurerm = azurerm.prod_central
  }
  
  name_prefix = local.name_prefix
  location    = var.azure_location
  
  resource_group_name = module.azure_networking.resource_group_name
  
  enable_versioning = true
  enable_encryption = var.enable_security
  
  storage_accounts = {
    "${local.name_prefix}-data" = {
      account_tier             = "Standard"
      access_tier             = "Hot"
      enable_hierarchical_namespace = true
    },
    "${local.name_prefix}-backups" = {
      account_tier = "Cool"
      access_tier   = "Cold"
    }
  }
  
  key_vault_id = data.azurerm_key_vault.main.id
  
  tags = local.common_tags
}

module "gcp_storage" {
  source = "../../modules/gcp-storage"
  
  providers = {
    google = google.prod_central
  }
  
  name_prefix = local.name_prefix
  project_id  = var.gcp_project_id
  location    = var.gcp_region
  
  enable_versioning = true
  enable_encryption = var.enable_security
  
  buckets = {
    "${local.name_prefix}-app-data" = {
      versioning_enabled = true
      lifecycle_enabled = true
      location          = "US-CENTRAL1"
    },
    "${local.name_prefix}-backups" = {
      versioning_enabled = true
      lifecycle_enabled = true
      location          = "US-CENTRAL1"
      storage_class      = "NEARLINE"
    }
  }
  
  kms_key_name = "${local.name_prefix}-storage-key"
  
  tags = local.common_tags
}

# ------------------------------------------------------------------------
# MONITORING LAYER
# ------------------------------------------------------------------------

module "aws_monitoring" {
  source = "../../modules/aws-monitoring"
  
  providers = {
    aws = aws.prod_east
  }
  
  name_prefix = local.name_prefix
  environment = var.environment
  
  log_group_name = "${local.name_prefix}-logs"
  
  enable_cloudwatch = var.enable_monitoring
  enable_xray     = var.enable_monitoring
  
  tags = local.common_tags
}

module "azure_monitoring" {
  source = "../../modules/azure-monitoring"
  
  providers = {
    azurerm = azurerm.prod_central
  }
  
  name_prefix = local.name_prefix
  location    = var.azure_location
  
  resource_group_name = module.azure_networking.resource_group_name
  
  log_analytics_workspace_name = "${local.name_prefix}-logs"
  
  enable_monitoring = var.enable_monitoring
  
  tags = local.common_tags
}

module "gcp_monitoring" {
  source = "../../modules/gcp-monitoring"
  
  providers = {
    google = google.prod_central
  }
  
  name_prefix = local.name_prefix
  project_id  = var.gcp_project_id
  
  enable_logging = var.enable_monitoring
  enable_monitoring = var.enable_monitoring
  
  tags = local.common_tags
}

# ------------------------------------------------------------------------
# OUTPUTS
# ------------------------------------------------------------------------

output "aws_network_info" {
  description = "AWS networking configuration"
  value = {
    vpc_id              = module.aws_networking.vpc_id
    vpc_cidr            = module.aws_networking.vpc_cidr
    public_subnet_ids   = module.aws_networking.public_subnet_ids
    private_subnet_ids  = module.aws_networking.private_subnet_ids
    availability_zones   = module.aws_networking.availability_zones
  internet_gateway_id = module.aws_networking.internet_gateway_id
    nat_gateway_ids    = module.aws_networking.nat_gateway_ids
  route_table_ids    = module.aws_networking.route_table_ids
  security_group_ids  = module.aws_security.security_group_ids
  tags              = local.common_tags
  }
}

output "azure_network_info" {
  description = "Azure networking configuration"
  value = {
    vnet_id            = module.azure_networking.vnet_id
    vnet_cidr          = module.azure_networking.vnet_cidr
    subnet_ids         = module.azure_networking.subnet_ids
    network_security_group_ids = module.azure_networking.network_security_group_ids
    route_table_ids    = module.azure_networking.route_table_ids
    tags               = local.common_tags
  }
}

output "gcp_network_info" {
  description = "GCP networking configuration"
  value = {
    network_name       = module.gcp_networking.network_name
    network_self_link = module.gcp_networking.network_self_link
    subnetwork_ids     = module.gcp_networking.subnetwork_ids
    firewall_ids       = module.gcp_security.firewall_ids
    routes_ids         = module.gcp_networking.route_ids
    tags              = local.common_tags
  }
}

output "compute_info" {
  description = "Compute resources across all clouds"
  value = {
    aws_instances    = module.aws_compute.instance_ids
    azure_vms        = module.azure_compute.vm_ids
    gcp_instances    = module.gcp_compute.instance_ids
    total_instances  = module.aws_compute.instance_count + module.azure_compute.vm_count + module.gcp_compute.instance_count
    tags            = local.common_tags
  }
}

output "database_info" {
  description = "Database resources across all clouds"
  value = {
    aws_databases   = module.aws_database.database_ids
    azure_databases  = module.azure_database.database_ids
    gcp_databases   = module.gcp_database.database_ids
    total_databases = module.aws_database.database_count + module.azure_database.database_count + module.gcp_database.database_count
    tags           = local.common_tags
  }
}

output "storage_info" {
  description = "Storage resources across all clouds"
  value = {
    aws_buckets     = module.aws_storage.bucket_ids
    azure_accounts  = module.azure_storage.account_ids
    gcp_buckets     = module.gcp_storage.bucket_ids
    total_storage   = length(keys(module.aws_storage.buckets)) + length(keys(module.azure_storage.accounts)) + length(keys(module.gcp_storage.buckets))
    tags           = local.common_tags
  }
}

output "monitoring_info" {
  description = "Monitoring configuration across all clouds"
  value = {
    aws_log_groups    = module.aws_monitoring.log_group_names
    azure_workspaces  = module.azure_monitoring.workspace_ids
    gcp_sinks        = module.gcp_monitoring.sink_ids
    tags            = local.common_tags
  }
}

output "resource_summary" {
  description = "Summary of all provisioned resources"
  value = {
    total_resources = (
      length(keys(module.aws_networking.route_table_ids)) +
      length(keys(module.azure_networking.route_table_ids)) +
      length(keys(module.gcp_networking.route_ids)) +
      module.aws_compute.instance_count +
      module.azure_compute.vm_count +
      module.gcp_compute.instance_count +
      module.aws_database.database_count +
      module.azure_database.database_count +
      module.gcp_database.database_count +
      length(keys(module.aws_storage.buckets)) +
      length(keys(module.azure_storage.accounts)) +
      length(keys(module.gcp_storage.buckets))
    )
    environment = var.environment
    project     = var.project_name
    providers   = ["aws", "azure", "gcp"]
    tags       = local.common_tags
  }
}
