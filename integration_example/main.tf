# =============================================================================
# Production MLOps + AIOps Platform on AWS — Boilerplate
# =============================================================================
# Copy this folder as a starting point for your own project. The included
# GitHub workflow keeps your architecture diagram, PR comments, and Confluence
# page in sync on every push.
#
# Stack: VPC → S3 Data Lake → Glue ETL → SageMaker Feature Store → EKS Training
#        → Model Registry (ECR + S3) → SageMaker Endpoints → CloudWatch AIOps
# =============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      Team        = "ml-platform"
      CostCenter  = "cc-12345"
      ManagedBy   = "terraform"
      Owner       = "platform@example.com"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {}

# -----------------------------------------------------------------------------
# Network — VPC with public/private subnets
# -----------------------------------------------------------------------------
resource "aws_vpc" "ml_vpc" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "${var.project}-vpc"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.ml_vpc.id
  tags = {
    Name = "${var.project}-igw"
  }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.ml_vpc.id
  cidr_block              = "10.20.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  tags = {
    Name = "${var.project}-public-a"
    Tier = "public"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.ml_vpc.id
  cidr_block              = "10.20.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true
  tags = {
    Name = "${var.project}-public-b"
    Tier = "public"
  }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.ml_vpc.id
  cidr_block        = "10.20.10.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]
  tags = {
    Name = "${var.project}-private-a"
    Tier = "private"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.ml_vpc.id
  cidr_block        = "10.20.11.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]
  tags = {
    Name = "${var.project}-private-b"
    Tier = "private"
  }
}

resource "aws_eip" "nat" {
  domain = "vpc"
  tags = {
    Name = "${var.project}-nat-eip"
  }
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_a.id
  depends_on    = [aws_internet_gateway.igw]
  tags = {
    Name = "${var.project}-nat"
  }
}

resource "aws_security_group" "sagemaker_sg" {
  name   = "${var.project}-sagemaker-sg"
  vpc_id = aws_vpc.ml_vpc.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {
    Name = "${var.project}-sagemaker-sg"
  }
}

resource "aws_security_group" "eks_sg" {
  name   = "${var.project}-eks-sg"
  vpc_id = aws_vpc.ml_vpc.id
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.sagemaker_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {
    Name = "${var.project}-eks-sg"
  }
}

resource "aws_security_group" "rds_sg" {
  name   = "${var.project}-rds-sg"
  vpc_id = aws_vpc.ml_vpc.id
  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_sg.id]
  }
  tags = {
    Name = "${var.project}-rds-sg"
  }
}

resource "aws_network_acl" "private_nacl" {
  vpc_id     = aws_vpc.ml_vpc.id
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = "10.20.0.0/16"
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
    Name = "${var.project}-private-nacl"
  }
}

# -----------------------------------------------------------------------------
# Storage — S3 Data Lake (raw → processed → curated), model registry
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "raw" {
  bucket = "${var.project}-raw-${data.aws_caller_identity.current.account_id}"
  tags = {
    Name    = "raw"
    Purpose = "Raw Data Lake"
  }
}

resource "aws_s3_bucket" "processed" {
  bucket = "${var.project}-processed-${data.aws_caller_identity.current.account_id}"
  tags = {
    Name    = "processed"
    Purpose = "Processed Features"
  }
}

resource "aws_s3_bucket" "models" {
  bucket = "${var.project}-models-${data.aws_caller_identity.current.account_id}"
  tags = {
    Name    = "models"
    Purpose = "Model Registry"
  }
}

resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "curated" {
  bucket = "${var.project}-curated-${data.aws_caller_identity.current.account_id}"
  tags = {
    Name    = "curated"
    Purpose = "Curated Lake"
  }
}

# -----------------------------------------------------------------------------
# Feature Store — Aurora MySQL + ElastiCache + DynamoDB
# -----------------------------------------------------------------------------
resource "aws_db_subnet_group" "aurora" {
  name       = "${var.project}-aurora-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  tags = {
    Name = "${var.project}-aurora-subnet-group"
  }
}

resource "aws_rds_cluster" "features" {
  cluster_identifier            = "${var.project}-features"
  engine                        = "aurora-mysql"
  engine_version                = "8.0.mysql_aurora.3.04.0"
  master_username               = "admin"
  master_password               = var.db_password
  db_subnet_group_name          = aws_db_subnet_group.aurora.name
  vpc_security_group_ids        = [aws_security_group.rds_sg.id]
  backup_retention_period       = 7
  preferred_backup_window       = "03:00-04:00"
  enabled_cloudwatch_logs_exports = ["audit", "error"]
  tags = {
    Name = "${var.project}-features"
  }
}

resource "aws_elasticache_subnet_group" "cache" {
  name       = "${var.project}-cache-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

resource "aws_elasticache_cluster" "online" {
  cluster_id           = "${var.project}-online-cache"
  engine               = "redis"
  node_type            = "cache.r6g.large"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  subnet_group_name    = aws_elasticache_subnet_group.cache.name
  security_group_ids   = [aws_security_group.eks_sg.id]
  tags = {
    Name = "${var.project}-online-cache"
  }
}

resource "aws_dynamodb_table" "experiments" {
  name         = "${var.project}-experiments"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "experiment_id"
  range_key    = "created_at"
  attribute {
    name = "experiment_id"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "N"
  }
  point_in_time_recovery {
    enabled = true
  }
  tags = {
    Name = "${var.project}-experiments"
  }
}

# -----------------------------------------------------------------------------
# ETL — Glue Catalog + Crawler + Job + Kinesis ingestion
# -----------------------------------------------------------------------------
resource "aws_glue_catalog_database" "lake" {
  name = "${var.project}_lake"
}

resource "aws_kinesis_stream" "ingest" {
  name             = "${var.project}-ingest"
  shard_count      = 2
  retention_period = 24
  tags = {
    Name = "ingest-stream"
  }
}

resource "aws_glue_crawler" "raw" {
  database_name = aws_glue_catalog_database.lake.name
  name          = "${var.project}-raw-crawler"
  role          = aws_iam_role.glue_role.arn
  s3_target {
    path = "s3://${aws_s3_bucket.raw.bucket}"
  }
}

resource "aws_glue_job" "feature_job" {
  name     = "${var.project}-feature-job"
  role_arn = aws_iam_role.glue_role.arn
  command {
    script_location = "s3://${aws_s3_bucket.raw.bucket}/scripts/feature.py"
    python_version  = "3"
  }
  glue_version      = "4.0"
  number_of_workers = 2
  worker_type       = "G.1X"
  tags = {
    Name = "${var.project}-feature-job"
  }
}

# -----------------------------------------------------------------------------
# Compute — EKS (training), ECR, Lambda (pre-processing & AIOps remediation)
# -----------------------------------------------------------------------------
resource "aws_ecr_repository" "trainer" {
  name = "${var.project}/trainer"
  image_scanning_configuration {
    scan_on_push = true
  }
  tags = {
    Name = "${var.project}-trainer"
  }
}

resource "aws_eks_cluster" "ml" {
  name     = "${var.project}-eks"
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = "1.29"
  vpc_config {
    subnet_ids              = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_group_ids      = [aws_security_group.eks_sg.id]
    endpoint_private_access = true
    endpoint_public_access  = true
  }
  enabled_cluster_log_types = ["api", "audit"]
  tags = {
    Name = "${var.project}-eks"
  }
  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster
  ]
}

resource "aws_eks_node_group" "gpu" {
  cluster_name    = aws_eks_cluster.ml.name
  node_group_name = "${var.project}-gpu"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  instance_types  = ["p3.2xlarge"]
  scaling_config {
    desired_size = 2
    max_size     = 6
    min_size     = 1
  }
  tags = {
    Name = "${var.project}-gpu-nodes"
  }
  depends_on = [
    aws_iam_role_policy_attachment.eks_worker,
    aws_iam_role_policy_attachment.eks_cni,
    aws_iam_role_policy_attachment.eks_registry
  ]
}

resource "aws_lambda_function" "preprocess" {
  function_name = "${var.project}-preprocess"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  filename      = "lambda.zip"
  timeout       = 300
  memory_size   = 1024
  vpc_config {
    subnet_ids         = [aws_subnet.private_a.id]
    security_group_ids = [aws_security_group.sagemaker_sg.id]
  }
  environment {
    variables = {
      RAW_BUCKET       = aws_s3_bucket.raw.id
      PROCESSED_BUCKET = aws_s3_bucket.processed.id
    }
  }
  tags = {
    Name = "${var.project}-preprocess"
  }
}

resource "aws_lambda_function" "remediator" {
  function_name = "${var.project}-aiops-remediator"
  role          = aws_iam_role.lambda_role.arn
  handler       = "remediator.handler"
  runtime       = "python3.11"
  filename      = "lambda.zip"
  timeout       = 60
  environment {
    variables = {
      SNS_TOPIC = aws_sns_topic.alerts.arn
    }
  }
  tags = {
    Name    = "${var.project}-remediator"
    Purpose = "AIOps auto-remediation"
  }
}

# -----------------------------------------------------------------------------
# Orchestration — Step Functions + EventBridge + DLQ
# -----------------------------------------------------------------------------
resource "aws_sfn_state_machine" "pipeline" {
  name     = "${var.project}-pipeline"
  role_arn = aws_iam_role.sfn_role.arn
  definition = jsonencode({
    Comment = "MLOps pipeline"
    StartAt = "Preprocess"
    States = {
      Preprocess = {
        Type     = "Task"
        Resource = aws_lambda_function.preprocess.arn
        Next     = "GlueJob"
      }
      GlueJob = {
        Type     = "Task"
        Resource = "arn:aws:states:::glue:startJobRun.sync"
        Parameters = {
          JobName = aws_glue_job.feature_job.name
        }
        Next = "Train"
      }
      Train = {
        Type     = "Task"
        Resource = "arn:aws:states:::sagemaker:createTrainingJob.sync"
        End      = true
      }
    }
  })
  tags = {
    Name = "${var.project}-pipeline"
  }
}

resource "aws_cloudwatch_event_rule" "nightly" {
  name                = "${var.project}-nightly-train"
  schedule_expression = "cron(0 2 * * ? *)"
  tags = {
    Name = "${var.project}-nightly"
  }
}

resource "aws_cloudwatch_event_target" "nightly" {
  rule     = aws_cloudwatch_event_rule.nightly.name
  arn      = aws_sfn_state_machine.pipeline.arn
  role_arn = aws_iam_role.events_role.arn
}

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project}-dlq"
  message_retention_seconds = 1209600
  tags = {
    Name    = "${var.project}-dlq"
    Purpose = "DLQ for AIOps"
  }
}

resource "aws_sns_topic" "alerts" {
  name = "${var.project}-alerts"
  tags = {
    Name = "${var.project}-alerts"
  }
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_sns_topic_subscription" "alerts_lambda" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.remediator.arn
}

resource "aws_lambda_permission" "sns" {
  statement_id  = "AllowSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.remediator.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.alerts.arn
}

resource "aws_lambda_event_source_mapping" "kinesis" {
  event_source_arn  = aws_kinesis_stream.ingest.arn
  function_name     = aws_lambda_function.preprocess.arn
  starting_position = "LATEST"
  batch_size        = 100
}

# -----------------------------------------------------------------------------
# SageMaker — Domain, Feature Group, Model, Endpoint, Notebook
# -----------------------------------------------------------------------------
resource "aws_sagemaker_domain" "ml" {
  domain_name = "${var.project}-domain"
  auth_mode   = "IAM"
  vpc_id      = aws_vpc.ml_vpc.id
  subnet_ids  = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  default_user_settings {
    execution_role = aws_iam_role.sagemaker_role.arn
  }
  tags = {
    Name = "${var.project}-sagemaker-domain"
  }
}

resource "aws_sagemaker_feature_group" "store" {
  feature_group_name             = "${var.project}-store"
  record_identifier_feature_name = "id"
  event_time_feature_name        = "event_time"
  role_arn                       = aws_iam_role.sagemaker_role.arn
  feature_definition {
    feature_name = "id"
    feature_type = "String"
  }
  feature_definition {
    feature_name = "event_time"
    feature_type = "Fractional"
  }
  feature_definition {
    feature_name = "value"
    feature_type = "Fractional"
  }
  offline_store_config {
    s3_storage_config {
      s3_uri = "s3://${aws_s3_bucket.processed.bucket}/offline/"
    }
  }
  tags = {
    Name = "${var.project}-feature-group"
  }
}

resource "aws_sagemaker_model" "model" {
  name               = "${var.project}-model"
  execution_role_arn = aws_iam_role.sagemaker_role.arn
  primary_container {
    image = "${aws_ecr_repository.trainer.repository_url}:latest"
  }
  tags = {
    Name = "${var.project}-model"
  }
}

resource "aws_sagemaker_endpoint_configuration" "ep_config" {
  name = "${var.project}-ep-config"
  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.model.name
    initial_instance_count = 2
    instance_type          = "ml.m5.large"
  }
  tags = {
    Name = "${var.project}-ep-config"
  }
}

resource "aws_sagemaker_endpoint" "ep" {
  name                 = "${var.project}-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.ep_config.name
  tags = {
    Name = "${var.project}-endpoint"
  }
}

resource "aws_sagemaker_notebook_instance" "notebook" {
  name          = "${var.project}-notebook"
  role_arn      = aws_iam_role.sagemaker_role.arn
  instance_type = "ml.t3.medium"
  subnet_id     = aws_subnet.private_a.id
  security_groups = [aws_security_group.sagemaker_sg.id]
  tags = {
    Name = "${var.project}-notebook"
  }
}

# -----------------------------------------------------------------------------
# AIOps — CloudWatch, Alarms, Anomaly Detection, Automated Remediation
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "pipeline_logs" {
  name              = "/aws/${var.project}/pipeline"
  retention_in_days = 30
  tags = {
    Name = "${var.project}-pipeline-logs"
  }
}

resource "aws_cloudwatch_metric_alarm" "latency" {
  alarm_name          = "${var.project}-latency-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ModelLatency"
  namespace           = "${var.project}/Serving"
  period              = 60
  statistic           = "Average"
  threshold           = 200
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  tags = {
    Name = "${var.project}-latency-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "error_rate" {
  alarm_name          = "${var.project}-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Invocation5XXErrors"
  namespace           = "AWS/SageMaker"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_actions       = [aws_sns_topic.alerts.arn, aws_lambda_function.remediator.arn]
  tags = {
    Name = "${var.project}-error-alarm"
  }
}

resource "aws_cloudwatch_log_metric_filter" "training_failed" {
  name           = "${var.project}-training-failed"
  pattern        = "TrainingJobStatus=Failed"
  log_group_name = aws_cloudwatch_log_group.pipeline_logs.name
  metric_transformation {
    name      = "TrainingFailures"
    namespace = "${var.project}/Training"
    value     = "1"
  }
}

resource "aws_kms_key" "main" {
  description             = "${var.project} KMS"
  deletion_window_in_days = 10
  enable_key_rotation     = true
  tags = {
    Name = "${var.project}-kms"
  }
}

# -----------------------------------------------------------------------------
# IAM — least-privilege roles (plumbing, not diagram nodes)
# -----------------------------------------------------------------------------
resource "aws_iam_role" "eks_cluster_role" {
  name = "${var.project}-eks-cluster"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
  tags = {
    Name = "${var.project}-eks-cluster-role"
  }
}

resource "aws_iam_role_policy_attachment" "eks_cluster" {
  role       = aws_iam_role.eks_cluster_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_iam_role" "eks_node_role" {
  name = "${var.project}-eks-node"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
  tags = {
    Name = "${var.project}-eks-node-role"
  }
}

resource "aws_iam_role_policy_attachment" "eks_worker" {
  role       = aws_iam_role.eks_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "eks_cni" {
  role       = aws_iam_role.eks_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "eks_registry" {
  role       = aws_iam_role.eks_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.project}-lambda"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
  tags = {
    Name = "${var.project}-lambda-role"
  }
}

resource "aws_iam_role" "glue_role" {
  name = "${var.project}-glue"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
    }]
  })
  tags = {
    Name = "${var.project}-glue-role"
  }
}

resource "aws_iam_role" "sagemaker_role" {
  name = "${var.project}-sagemaker"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "sagemaker.amazonaws.com" }
    }]
  })
  tags = {
    Name = "${var.project}-sagemaker-role"
  }
}

resource "aws_iam_role" "sfn_role" {
  name = "${var.project}-sfn"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "states.amazonaws.com" }
    }]
  })
  tags = {
    Name = "${var.project}-sfn-role"
  }
}

resource "aws_iam_role" "events_role" {
  name = "${var.project}-events"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "events.amazonaws.com" }
    }]
  })
  tags = {
    Name = "${var.project}-events-role"
  }
}
