# Complex MLOps Architecture - Multi-Region AWS
# Demonstrates: VPC grouping, multi-region, security layers, data pipelines, ML workflows

# ===== US-EAST-1 REGION - PRIMARY =====

# Primary VPC with public and private subnets
resource "aws_vpc" "primary_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name        = "mlops-primary-vpc"
    Environment = "production"
    Region      = "us-east-1"
  }
}

# Internet Gateway for primary VPC
resource "aws_internet_gateway" "primary_igw" {
  vpc_id = aws_vpc.primary_vpc.id
  
  tags = {
    Name = "mlops-primary-igw"
  }
}

# Public subnet for ALB and NAT Gateway
resource "aws_subnet" "primary_public_subnet_1a" {
  vpc_id                  = aws_vpc.primary_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
  
  tags = {
    Name = "mlops-public-1a"
    Tier = "public"
  }
}

resource "aws_subnet" "primary_public_subnet_1b" {
  vpc_id                  = aws_vpc.primary_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true
  
  tags = {
    Name = "mlops-public-1b"
    Tier = "public"
  }
}

# Private subnets for compute and ML workloads
resource "aws_subnet" "primary_private_subnet_1a" {
  vpc_id            = aws_vpc.primary_vpc.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "us-east-1a"
  
  tags = {
    Name = "mlops-private-compute-1a"
    Tier = "private"
  }
}

resource "aws_subnet" "primary_private_subnet_1b" {
  vpc_id            = aws_vpc.primary_vpc.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "us-east-1b"
  
  tags = {
    Name = "mlops-private-compute-1b"
    Tier = "private"
  }
}

# NAT Gateway for private subnet internet access
resource "aws_nat_gateway" "primary_nat" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.primary_public_subnet_1a.id
  
  tags = {
    Name = "mlops-primary-nat"
  }
  
  depends_on = [aws_internet_gateway.primary_igw]
}

resource "aws_eip" "nat_eip" {
  domain = "vpc"
  
  tags = {
    Name = "mlops-nat-eip"
  }
}

# Security Groups
resource "aws_security_group" "alb_sg" {
  name        = "mlops-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.primary_vpc.id
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "mlops-alb-sg"
  }
}

resource "aws_security_group" "eks_sg" {
  name        = "mlops-eks-sg"
  description = "Security group for EKS cluster"
  vpc_id      = aws_vpc.primary_vpc.id
  
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "mlops-eks-sg"
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "mlops-rds-sg"
  description = "Security group for RDS Aurora"
  vpc_id      = aws_vpc.primary_vpc.id
  
  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_sg.id]
  }
  
  tags = {
    Name = "mlops-rds-sg"
  }
}

# Network ACL for additional security
resource "aws_network_acl" "private_nacl" {
  vpc_id     = aws_vpc.primary_vpc.id
  subnet_ids = [
    aws_subnet.primary_private_subnet_1a.id,
    aws_subnet.primary_private_subnet_1b.id
  ]
  
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = "10.0.0.0/16"
    from_port  = 0
    to_port    = 65535
  }
  
  egress {
    protocol   = -1
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }
  
  tags = {
    Name = "mlops-private-nacl"
  }
}

# Application Load Balancer
resource "aws_lb" "mlops_alb" {
  name               = "mlops-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [
    aws_subnet.primary_public_subnet_1a.id,
    aws_subnet.primary_public_subnet_1b.id
  ]
  
  enable_deletion_protection = true
  enable_http2              = true
  
  tags = {
    Name = "mlops-alb"
  }
}

# EKS Cluster for ML workloads
resource "aws_eks_cluster" "mlops_cluster" {
  name     = "mlops-production-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = "1.28"
  
  vpc_config {
    subnet_ids = [
      aws_subnet.primary_private_subnet_1a.id,
      aws_subnet.primary_private_subnet_1b.id
    ]
    security_group_ids      = [aws_security_group.eks_sg.id]
    endpoint_private_access = true
    endpoint_public_access  = true
  }
  
  enabled_cluster_log_types = ["api", "audit", "authenticator"]
  
  tags = {
    Name = "mlops-eks-cluster"
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_service_policy
  ]
}

# EKS Node Group
resource "aws_eks_node_group" "mlops_nodes" {
  cluster_name    = aws_eks_cluster.mlops_cluster.name
  node_group_name = "mlops-gpu-nodes"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = [
    aws_subnet.primary_private_subnet_1a.id,
    aws_subnet.primary_private_subnet_1b.id
  ]
  
  instance_types = ["p3.2xlarge", "p3.8xlarge"]
  
  scaling_config {
    desired_size = 3
    max_size     = 10
    min_size     = 2
  }
  
  tags = {
    Name = "mlops-gpu-nodes"
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.eks_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_registry_policy
  ]
}

# RDS Aurora for metadata and feature store
resource "aws_rds_cluster" "feature_store" {
  cluster_identifier      = "mlops-feature-store"
  engine                  = "aurora-mysql"
  engine_version          = "8.0.mysql_aurora.3.04.0"
  database_name           = "feature_store"
  master_username         = "admin"
  master_password         = "ChangeMe123!"  # Use AWS Secrets Manager in production
  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"
  vpc_security_group_ids  = [aws_security_group.rds_sg.id]
  db_subnet_group_name    = aws_db_subnet_group.aurora_subnet_group.name
  
  enabled_cloudwatch_logs_exports = ["audit", "error", "slowquery"]
  
  tags = {
    Name = "mlops-feature-store"
  }
}

resource "aws_db_subnet_group" "aurora_subnet_group" {
  name       = "mlops-aurora-subnet-group"
  subnet_ids = [
    aws_subnet.primary_private_subnet_1a.id,
    aws_subnet.primary_private_subnet_1b.id
  ]
  
  tags = {
    Name = "mlops-aurora-subnet-group"
  }
}

# ElastiCache Redis for real-time feature serving
resource "aws_elasticache_cluster" "feature_cache" {
  cluster_id           = "mlops-feature-cache"
  engine               = "redis"
  node_type            = "cache.r6g.xlarge"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.cache_subnet_group.name
  security_group_ids   = [aws_security_group.eks_sg.id]
  
  tags = {
    Name = "mlops-feature-cache"
  }
}

resource "aws_elasticache_subnet_group" "cache_subnet_group" {
  name       = "mlops-cache-subnet-group"
  subnet_ids = [
    aws_subnet.primary_private_subnet_1a.id,
    aws_subnet.primary_private_subnet_1b.id
  ]
}

# S3 Buckets for data and models
resource "aws_s3_bucket" "training_data" {
  bucket = "mlops-training-data-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name        = "mlops-training-data"
    Purpose     = "Training Data Storage"
    Compliance  = "GDPR"
  }
}

resource "aws_s3_bucket" "model_artifacts" {
  bucket = "mlops-model-artifacts-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name    = "mlops-model-artifacts"
    Purpose = "Model Registry"
  }
}

resource "aws_s3_bucket" "data_lake" {
  bucket = "mlops-data-lake-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name    = "mlops-data-lake"
    Purpose = "Raw Data Lake"
  }
}

# S3 Versioning for model artifacts
resource "aws_s3_bucket_versioning" "model_versioning" {
  bucket = aws_s3_bucket.model_artifacts.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# DynamoDB for experiment tracking
resource "aws_dynamodb_table" "experiment_tracking" {
  name           = "mlops-experiment-tracking"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "experiment_id"
  range_key      = "timestamp"
  
  attribute {
    name = "experiment_id"
    type = "S"
  }
  
  attribute {
    name = "timestamp"
    type = "N"
  }
  
  attribute {
    name = "model_name"
    type = "S"
  }
  
  global_secondary_index {
    name            = "ModelNameIndex"
    hash_key        = "model_name"
    range_key       = "timestamp"
    projection_type = "ALL"
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  tags = {
    Name = "mlops-experiment-tracking"
  }
}

# Lambda for data preprocessing
resource "aws_lambda_function" "data_preprocessor" {
  filename         = "lambda_function.zip"
  function_name    = "mlops-data-preprocessor"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.handler"
  source_code_hash = filebase64sha256("lambda_function.zip")
  runtime          = "python3.11"
  timeout          = 900
  memory_size      = 3008
  
  vpc_config {
    subnet_ids         = [aws_subnet.primary_private_subnet_1a.id]
    security_group_ids = [aws_security_group.eks_sg.id]
  }
  
  environment {
    variables = {
      S3_BUCKET           = aws_s3_bucket.training_data.id
      FEATURE_STORE_HOST  = aws_rds_cluster.feature_store.endpoint
      REDIS_ENDPOINT      = aws_elasticache_cluster.feature_cache.cache_nodes[0].address
    }
  }
  
  tags = {
    Name = "mlops-data-preprocessor"
  }
}

# Step Functions for ML pipeline orchestration
resource "aws_sfn_state_machine" "ml_pipeline" {
  name     = "mlops-training-pipeline"
  role_arn = aws_iam_role.step_functions_role.arn
  
  definition = jsonencode({
    Comment = "MLOps Training Pipeline"
    StartAt = "DataPreprocessing"
    States = {
      DataPreprocessing = {
        Type     = "Task"
        Resource = aws_lambda_function.data_preprocessor.arn
        Next     = "ModelTraining"
      }
      ModelTraining = {
        Type     = "Task"
        Resource = "arn:aws:states:::sagemaker:createTrainingJob.sync"
        Next     = "ModelEvaluation"
      }
      ModelEvaluation = {
        Type     = "Task"
        Resource = aws_lambda_function.model_evaluator.arn
        Next     = "DeploymentDecision"
      }
      DeploymentDecision = {
        Type = "Choice"
        Choices = [{
          Variable      = "$.accuracy"
          NumericGreaterThan = 0.95
          Next          = "DeployModel"
        }]
        Default = "NotifyFailure"
      }
      DeployModel = {
        Type     = "Task"
        Resource = "arn:aws:states:::sagemaker:createEndpoint"
        End      = true
      }
      NotifyFailure = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        End      = true
      }
    }
  })
  
  tags = {
    Name = "mlops-training-pipeline"
  }
}

# Lambda for model evaluation
resource "aws_lambda_function" "model_evaluator" {
  filename         = "lambda_function.zip"
  function_name    = "mlops-model-evaluator"
  role             = aws_iam_role.lambda_role.arn
  handler          = "evaluator.handler"
  source_code_hash = filebase64sha256("lambda_function.zip")
  runtime          = "python3.11"
  timeout          = 300
  memory_size      = 1024
  
  environment {
    variables = {
      MODEL_BUCKET    = aws_s3_bucket.model_artifacts.id
      DYNAMODB_TABLE  = aws_dynamodb_table.experiment_tracking.name
    }
  }
  
  tags = {
    Name = "mlops-model-evaluator"
  }
}

# SageMaker for model training
resource "aws_sagemaker_notebook_instance" "ml_notebook" {
  name                    = "mlops-notebook"
  role_arn                = aws_iam_role.sagemaker_role.arn
  instance_type           = "ml.t3.xlarge"
  subnet_id               = aws_subnet.primary_private_subnet_1a.id
  security_groups         = [aws_security_group.eks_sg.id]
  direct_internet_access  = "Disabled"
  
  tags = {
    Name = "mlops-notebook"
  }
}

# SNS for alerts
resource "aws_sns_topic" "ml_alerts" {
  name = "mlops-alerts"
  
  tags = {
    Name = "mlops-alerts"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ml_pipeline_logs" {
  name              = "/aws/mlops/pipeline"
  retention_in_days = 30
  
  tags = {
    Name = "mlops-pipeline-logs"
  }
}

# KMS Key for encryption
resource "aws_kms_key" "mlops_key" {
  description             = "KMS key for MLOps encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true
  
  tags = {
    Name = "mlops-kms-key"
  }
}

# IAM Roles
resource "aws_iam_role" "eks_cluster_role" {
  name = "mlops-eks-cluster-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

resource "aws_iam_role_policy_attachment" "eks_service_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

resource "aws_iam_role" "eks_node_role" {
  name = "mlops-eks-node-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role" "lambda_role" {
  name = "mlops-lambda-role"
  
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
  name = "mlops-step-functions-role"
  
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

resource "aws_iam_role" "sagemaker_role" {
  name = "mlops-sagemaker-role"
  
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

# ===== US-WEST-2 REGION - DISASTER RECOVERY =====

# DR VPC
resource "aws_vpc" "dr_vpc" {
  provider             = aws.us-west-2
  cidr_block           = "10.1.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name        = "mlops-dr-vpc"
    Environment = "disaster-recovery"
    Region      = "us-west-2"
  }
}

# DR Subnets
resource "aws_subnet" "dr_private_subnet_2a" {
  provider          = aws.us-west-2
  vpc_id            = aws_vpc.dr_vpc.id
  cidr_block        = "10.1.10.0/24"
  availability_zone = "us-west-2a"
  
  tags = {
    Name = "mlops-dr-private-2a"
    Tier = "private"
  }
}

# VPC Peering between regions
resource "aws_vpc_peering_connection" "primary_to_dr" {
  vpc_id        = aws_vpc.primary_vpc.id
  peer_vpc_id   = aws_vpc.dr_vpc.id
  peer_region   = "us-west-2"
  auto_accept   = false
  
  tags = {
    Name = "mlops-primary-to-dr-peering"
  }
}

resource "aws_vpc_peering_connection_accepter" "dr_accepter" {
  provider                  = aws.us-west-2
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_dr.id
  auto_accept               = true
  
  tags = {
    Name = "mlops-dr-peering-accepter"
  }
}

# DR RDS Read Replica
resource "aws_rds_cluster" "feature_store_replica" {
  provider                = aws.us-west-2
  cluster_identifier      = "mlops-feature-store-replica"
  engine                  = "aurora-mysql"
  replication_source_identifier = aws_rds_cluster.feature_store.arn
  vpc_security_group_ids  = [aws_security_group.eks_sg.id]
  
  tags = {
    Name = "mlops-feature-store-replica"
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Provider configuration
provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "us-west-2"
  region = "us-west-2"
}
