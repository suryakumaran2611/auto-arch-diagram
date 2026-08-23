terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Network
resource "aws_vpc" "app_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "gemini-demo-vpc"
  }
}

resource "aws_subnet" "public_1" {
  vpc_id            = aws_vpc.app_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.app_vpc.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "us-east-1a"
}

# Compute - AWS App Runner & ECS Fargate
resource "aws_apprunner_service" "api_service" {
  service_name = "gemini-ai-api"

  source_configuration {
    image_repository {
      image_identifier      = "public.ecr.aws/aws-containers/hello-app-runner:latest"
      image_repository_type = "ECR_PUBLIC"
    }
  }
}

# Ingress / API Gateway
resource "aws_apigatewayv2_api" "http_api" {
  name          = "gemini-http-gateway"
  protocol_type = "HTTP"
}

# Storage & Database
resource "aws_s3_bucket" "artifacts_bucket" {
  bucket = "gemini-demo-artifacts-bucket-2026"
}

resource "aws_elasticache_cluster" "redis_cache" {
  cluster_id           = "gemini-redis-cache"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
}

resource "aws_rds_cluster" "aurora_postgres" {
  cluster_identifier = "gemini-aurora-pg"
  engine             = "aurora-postgresql"
  database_name      = "production"
  master_username    = "dbadmin"
  master_password    = "SecurePassword2026!"
}

# Security & KMS
resource "aws_kms_key" "app_encryption_key" {
  description             = "KMS Key for Gemini Demo Data Encryption"
  deletion_window_in_days = 7
}
