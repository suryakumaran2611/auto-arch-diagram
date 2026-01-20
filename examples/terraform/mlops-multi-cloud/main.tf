# Simple Multi-Cloud Demo: Basic networking and storage across AWS, Azure, and GCP
# This demonstrates cross-cloud architecture patterns without complex dependencies

terraform {
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
      version = "~> 5.0"
    }
  }
}

# ===== AWS INFRASTRUCTURE =====

# AWS VPC for multi-cloud connectivity (Network: aws-network)
resource "aws_vpc" "vpc_aws_network" {
  provider             = aws
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name     = "vpc-aws-network"
    Purpose  = "Multi-Cloud Demo"
    Provider = "AWS"
    Network  = "aws-network"
  }
}

# AWS Subnet (Network: aws-network)
resource "aws_subnet" "subnet_aws_network" {
  provider          = aws
  vpc_id            = aws_vpc.vpc_aws_network.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name    = "subnet-aws-network"
    Network = "aws-network"
  }
}

# AWS S3 Bucket for shared data (Network: global)
resource "aws_s3_bucket" "s3_global" {
  provider = aws
  bucket   = "multi-cloud-demo-shared-data"

  tags = {
    Name     = "s3-global"
    Purpose  = "Cross-Cloud Data Sharing"
    Provider = "AWS"
    Network  = "global"
  }
}

# ===== AZURE INFRASTRUCTURE =====

# Azure Resource Group (Network: azure-network)
resource "azurerm_resource_group" "rg_azure_network" {
  provider = azurerm
  name     = "rg-azure-network"
  location = "East US"

  tags = {
    Environment = "demo"
    Project     = "multi-cloud"
    Network     = "azure-network"
  }
}

# Azure Storage Account for shared data (Network: global)
resource "azurerm_storage_account" "storage_global" {
  provider                 = azurerm
  name                     = "multicloudstorage"
  resource_group_name      = azurerm_resource_group.rg_azure_network.name
  location                 = azurerm_resource_group.rg_azure_network.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    Environment = "demo"
    Purpose     = "Cross-Cloud Data Sharing"
    Provider    = "Azure"
    Network     = "global"
  }
}

# Azure Storage Container (Network: global)
resource "azurerm_storage_container" "container_global" {
  provider              = azurerm
  name                  = "shared-data"
  storage_account_name  = azurerm_storage_account.storage_global.name
  container_access_type = "private"
}

# ===== GOOGLE CLOUD INFRASTRUCTURE =====

# GCP Storage Bucket for shared data (Network: global)
resource "google_storage_bucket" "bucket_global" {
  provider = google
  name     = "multi-cloud-demo-shared-data"
  location = "US"

  uniform_bucket_level_access = true

  labels = {
    environment = "demo"
    purpose     = "cross-cloud-data-sharing"
    provider    = "gcp"
    network     = "global"
  }
}

# ===== OUTPUTS =====

output "aws_s3_bucket" {
  description = "AWS S3 bucket for shared data (Network: global)"
  value       = aws_s3_bucket.s3_global.bucket
}

output "azure_storage_account" {
  description = "Azure storage account name (Network: global)"
  value       = azurerm_storage_account.storage_global.name
}

output "azure_storage_primary_endpoint" {
  description = "Azure storage primary endpoint (Network: global)"
  value       = azurerm_storage_account.storage_global.primary_blob_endpoint
}

output "gcp_storage_bucket" {
  description = "GCP storage bucket name (Network: global)"
  value       = google_storage_bucket.bucket_global.name
}