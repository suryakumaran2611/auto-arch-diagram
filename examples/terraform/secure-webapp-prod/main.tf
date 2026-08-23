###############################################################################
# Secure Production Web Application - reference architecture
#
# Standards applied:
#   - Multi-AZ VPC with isolated private application and data tiers
#   - WAF protection in front of the public ALB, HTTPS-only listeners
#   - Least-privilege IAM roles for ECS task and execution
#   - Encrypted data stores (KMS CMK): RDS, ElastiCache, S3, logs
#   - Secrets managed via AWS Secrets Manager, rotated config via SSM
#   - Immutable container image tags with automatic vulnerability scanning
#   - Centralized logging with retention and alerting via SNS
###############################################################################

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
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Compliance  = "baseline-security-v2"
    }
  }
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Primary deployment region."
}

variable "vpc_cidr" {
  type        = string
  default     = "10.40.0.0/16"
  description = "CIDR block for the application VPC."
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN for HTTPS termination on the ALB."
}

variable "project_name" {
  type        = string
  default     = "shop"
  description = "Project short name used for resource naming."
}

variable "environment" {
  type        = string
  default     = "prod"
  description = "Deployment environment."
}

variable "container_image" {
  type        = string
  description = "Container image for the web application service."
}

variable "app_port" {
  type        = number
  default     = 8080
  description = "Port the container listens on."
}

variable "alarm_email" {
  type        = string
  description = "Operations email endpoint for CloudWatch alarms."
}

# ---------------------------------------------------------------------------
# Networking: multi-AZ VPC, segregated tiers
# ---------------------------------------------------------------------------

resource "aws_vpc" "app_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-vpc" })
}

resource "aws_internet_gateway" "app_igw" {
  vpc_id = aws_vpc.app_vpc.id

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-igw" })
}

resource "aws_subnet" "public_subnet_az1" {
  vpc_id                  = aws_vpc.app_vpc.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, 0)
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = false

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-public-az1", Tier = "edge" })
}

resource "aws_subnet" "public_subnet_az2" {
  vpc_id                  = aws_vpc.app_vpc.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, 1)
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = false

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-public-az2", Tier = "edge" })
}

resource "aws_subnet" "private_app_subnet_az1" {
  vpc_id            = aws_vpc.app_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 2)
  availability_zone = "${var.aws_region}a"

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-private-app-az1", Tier = "application" })
}

resource "aws_subnet" "private_app_subnet_az2" {
  vpc_id            = aws_vpc.app_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 3)
  availability_zone = "${var.aws_region}b"

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-private-app-az2", Tier = "application" })
}

resource "aws_subnet" "private_data_subnet_az1" {
  vpc_id            = aws_vpc.app_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 4)
  availability_zone = "${var.aws_region}a"

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-private-data-az1", Tier = "data" })
}

resource "aws_subnet" "private_data_subnet_az2" {
  vpc_id            = aws_vpc.app_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 5)
  availability_zone = "${var.aws_region}b"

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-private-data-az2", Tier = "data" })
}

resource "aws_eip" "nat_gw_elastic_ip_az1" {
  domain = "vpc"

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-nat-eip-az1" })
}

resource "aws_nat_gateway" "app_nat_gw_az1" {
  allocation_id = aws_eip.nat_gw_elastic_ip_az1.id
  subnet_id     = aws_subnet.public_subnet_az1.id

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-nat-az1" })

  depends_on = [aws_internet_gateway.app_igw]
}

resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.app_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.app_igw.id
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-public-rt" })
}

resource "aws_route_table" "private_route_table" {
  vpc_id = aws_vpc.app_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.app_nat_gw_az1.id
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-private-rt" })
}

resource "aws_route_table_association" "public_rt_assoc_az1" {
  subnet_id      = aws_subnet.public_subnet_az1.id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "public_rt_assoc_az2" {
  subnet_id      = aws_subnet.public_subnet_az2.id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "private_rt_assoc_az1" {
  subnet_id      = aws_subnet.private_app_subnet_az1.id
  route_table_id = aws_route_table.private_route_table.id
}

resource "aws_route_table_association" "private_rt_assoc_az2" {
  subnet_id      = aws_subnet.private_app_subnet_az2.id
  route_table_id = aws_route_table.private_route_table.id
}

# ---------------------------------------------------------------------------
# Encryption: customer-managed KMS keys with rotation
# ---------------------------------------------------------------------------

resource "aws_kms_key" "data_encryption_key" {
  description             = "CMK for ${local.name_prefix} data stores"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-kms" })
}

resource "aws_kms_alias" "data_encryption_key_alias" {
  name          = "alias/${local.name_prefix}-data-key"
  target_key_id = aws_kms_key.data_encryption_key.key_id
}

# ---------------------------------------------------------------------------
# Edge security: WAF attached to the ALB
# ---------------------------------------------------------------------------

resource "aws_wafv2_web_acl" "alb_web_acl" {
  name  = "${local.name_prefix}-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name         = "AWS"
        name                = "AWSManagedRulesCommonRuleSet"
        excluded_rule { name = "SizeRestrictions_BODY" }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-common-rules"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimitPerIP"
    priority = 2

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregateKeyType   = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-waf-default"
    sampled_requests_enabled   = true
  }
}

# ---------------------------------------------------------------------------
# Load balancing: internet-facing ALB, HTTPS only
# ---------------------------------------------------------------------------

resource "aws_security_group" "alb_security_group" {
  name_prefix = "${local.name_prefix}-alb-"
  vpc_id      = aws_vpc.app_vpc.id

  ingress {
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
    description      = "HTTPS from anywhere (WAF filters malicious traffic)"
  }

  egress {
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    security_groups = [aws_security_group.ecs_tasks_security_group.id]
    description = "Application traffic to ECS tasks only"
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-alb-sg" })
}

resource "aws_security_group" "ecs_tasks_security_group" {
  name_prefix = "${local.name_prefix}-ecs-"
  vpc_id      = aws_vpc.app_vpc.id

  ingress {
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_security_group.id]
    description     = "App traffic from ALB only"
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    prefix_list_ids = []
    cidr_blocks = ["0.0.0.0/0"]
    description = "TLS egress (AWS APIs, external integrations)"
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-ecs-sg" })
}

resource "aws_lb" "app_alb" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_security_group.id]
  subnets            = [aws_subnet.public_subnet_az1.id, aws_subnet.public_subnet_az2.id]

  drop_invalid_header_fields = true

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-alb" })
}

resource "aws_lb_target_group" "app_target_group" {
  name        = "${local.name_prefix}-tg"
  port        = var.app_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.app_vpc.id
  target_type = "ip"

  health_check {
    path                = "/healthz"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-tg" })
}

resource "aws_lb_listener" "https_listener" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    forward {
      target_group_arn = aws_lb_target_group.app_target_group.arn
    }
  }

  depends_on = [aws_wafv2_web_acl.alb_web_acl]
}

resource "aws_lb_listener" "http_redirect_listener" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_wafv2_web_acl_association" "alb_waf_assoc" {
  resource_arn = aws_lb.app_alb.arn
  web_acl_arn  = aws_wafv2_web_acl.alb_web_acl.arn
}

# ---------------------------------------------------------------------------
# Compute: ECS Fargate service in private subnets
# ---------------------------------------------------------------------------

resource "aws_ecs_cluster" "app_cluster" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.common_tags
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${local.name_prefix}-ecs-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "ecs-tasks.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  name = "${local.name_prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "ecs-tasks.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_efs_access_point" "static_assets_ap" {
  file_system_id = aws_efs.app_file_system.id

  root_directory {
    path                 = "/static"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "0755"
    }
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-static-ap" })
}

resource "aws_ecs_task_definition" "app_task_definition" {
  family                   = "${local.name_prefix}-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  container_definitions = jsonencode([
    {
      name      = "web"
      image     = var.container_image
      essential = true
      portMappings = [
        {
          containerPort = var.app_port
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "APP_ENV", value = var.environment },
        { name = "DB_HOST_SECRET_ARN", value = aws_secretsmanager_secret.db_credentials_secret.arn }
      ]
      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = aws_secretsmanager_secret.db_credentials_secret.arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app_log_group.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "web"
        }
      }
    }
  ])

  tags = local.common_tags
}

resource "aws_ecs_service" "app_service" {
  name            = "${local.name_prefix}-service"
  cluster         = aws_ecs_cluster.app_cluster.id
  task_definition = aws_ecs_task_definition.app_task_definition.arn
  desired_count   = 3
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = [aws_subnet.private_app_subnet_az1.id, aws_subnet.private_app_subnet_az2.id]
    security_groups = [aws_security_group.ecs_tasks_security_group.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app_target_group.arn
    container_name   = "web"
    container_port   = var.app_port
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
}

resource "aws_ecr_repository" "app_repository" {
  name = "${local.name_prefix}/web"

  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

resource "aws_application_autoscaling_target" "service_scaling_target" {
  max_capacity       = 10
  min_capacity       = 3
  resource_id        = "service/${aws_ecs_cluster.app_cluster.name}/${aws_ecs_service.app_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# ---------------------------------------------------------------------------
# Shared file storage for static assets (EFS)
# ---------------------------------------------------------------------------

resource "aws_efs_file_system" "app_file_system" {
  encrypted = true
  kms_key_id = aws_kms_key.data_encryption_key.arn

  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-static-assets" })
}

resource "aws_security_group" "efs_security_group" {
  name_prefix = "${local.name_prefix}-efs-"
  vpc_id      = aws_vpc.app_vpc.id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks_security_group.id]
    description     = "NFS from app tier only"
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-efs-sg" })
}

resource "aws_efs_mount_target" "mount_az1" {
  file_system_id  = aws_efs.app_file_system.id
  subnet_id       = aws_subnet.private_app_subnet_az1.id
  security_groups = [aws_security_group.efs_security_group.id]
}

resource "aws_efs_mount_target" "mount_az2" {
  file_system_id  = aws_efs.app_file_system.id
  subnet_id       = aws_subnet.private_app_subnet_az2.id
  security_groups = [aws_security_group.efs_security_group.id]
}

# ---------------------------------------------------------------------------
# Data tier: RDS PostgreSQL (multi-AZ, encrypted) + ElastiCache Redis
# ---------------------------------------------------------------------------

resource "aws_db_subnet_group" "db_subnet_group" {
  name       = "${local.name_prefix}-dbsubnets"
  subnet_ids = [aws_subnet.private_data_subnet_az1.id, aws_subnet.private_data_subnet_az2.id]

  tags = local.common_tags
}

resource "random_password" "db_master_password" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret" "db_credentials_secret" {
  name                    = "${local.name_prefix}/db/master"
  kms_key_id              = aws_kms_key.data_encryption_key.key_id
  recovery_window_in_days = 7

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "db_credentials_version" {
  secret_id = aws_secretsmanager_secret.db_credentials_secret.id
  secret_string = jsonencode({
    username = "appadmin"
    password = random_password.db_master_password.result
    host     = aws_db_instance.postgres_db.address
    dbname   = "appdb"
  })
}

resource "aws_security_group" "db_security_group" {
  name_prefix = "${local.name_prefix}-db-"
  vpc_id      = aws_vpc.app_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks_security_group.id]
    description     = "PostgreSQL from app tier only"
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-db-sg" })
}

resource "aws_ssm_parameter" "app_feature_flags" {
  name        = "/${local.name_prefix}/feature-flags"
  description = "Runtime feature flags for the web application"
  type        = "String"
  value       = "{}"

  tags = local.common_tags
}

resource "aws_db_instance" "postgres_db" {
  identifier     = "${local.name_prefix}-postgres"
  engine         = "postgres"
  engine_version = "15"
  instance_class = "db.t4g.medium"

  allocated_storage     = 50
  max_allocated_storage = 500
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.data_encryption_key.arn

  db_name  = "appdb"
  username = "appadmin"
  password = random_password.db_master_password.result

  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.db_subnet_group.name
  vpc_security_group_ids = [aws_security_group.db_security_group.id]

  backup_retention_period   = 14
  backup_window             = "03:00-04:00"
  copy_tags_to_snapshot     = true
  delete_automated_backups  = false
  deletion_protection       = true
  auto_minor_version_upgrade = true

  performance_insights_enabled = true

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-postgres" })
}

resource "aws_security_group" "redis_security_group" {
  name_prefix = "${local.name_prefix}-redis-"
  vpc_id      = aws_vpc.app_vpc.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks_security_group.id]
    description     = "Redis from app tier only"
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-redis-sg" })
}

resource "aws_elasticache_subnet_group" "cache_subnet_group" {
  name       = "${local.name_prefix}-cache-subnets"
  subnet_ids = [aws_subnet.private_data_subnet_az1.id, aws_subnet.private_data_subnet_az2.id]
}

resource "aws_elasticache_replication_group" "redis_replication_group" {
  replication_group_id       = "${local.name_prefix}-redis"
  description                = "Session cache and job queue backing store"
  engine                     = "redis"
  engine_version             = "7.0"
  node_type                  = "cache.t4g.small"
  num_node_groups            = 1
  replicas_per_node_group    = 1
  automatic_failover_enabled = true
  multi_az_enabled           = true

  subnet_group_name  = aws_elasticache_subnet_group.cache_subnet_group.name
  security_group_ids = [aws_security_group.redis_security_group.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  kms_key_id                 = aws_kms_key.data_encryption_key.arn

  snapshot_retention_limit = 7
  snapshot_window          = "05:00-06:00"

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-redis" })
}

# ---------------------------------------------------------------------------
# Object storage: private versioned assets bucket
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "assets_bucket" {
  bucket = "${local.name_prefix}-assets-${data.aws_caller_identity.current.account_id}"

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-assets" })
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket_versioning" "assets_versioning" {
  bucket = aws_s3_bucket.assets_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "assets_encryption" {
  bucket = aws_s3_bucket.assets_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data_encryption_key.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "assets_pab" {
  bucket = aws_s3_bucket.assets_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "assets_lifecycle" {
  bucket = aws_s3_bucket.assets_bucket.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# ---------------------------------------------------------------------------
# Observability: centralized logs, alarms and notifications
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "app_log_group" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = 365
  kms_key_id        = aws_kms_key.data_encryption_key.arn

  tags = local.common_tags
}

resource "aws_sns_topic" "ops_alerts_topic" {
  name = "${local.name_prefix}-ops-alerts"

  kms_master_key_id = aws_kms_key.data_encryption_key.key_id

  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "ops_email_subscription" {
  topic_arn = aws_sns_topic.ops_alerts_topic.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx_alarm" {
  alarm_name          = "${local.name_prefix}-alb-5xx-high"
  alarm_description   = "High rate of 5xx responses from the application"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 25

  dimensions = {
    LoadBalancer = aws_lb.app_alb.arn_suffix
  }

  alarm_actions = [aws_sns_topic.ops_alerts_topic.arn]

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu_alarm" {
  alarm_name          = "${local.name_prefix}-rds-cpu-high"
  alarm_description   = "RDS CPU utilization above sustainable level"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres_db.identifier
  }

  alarm_actions = [aws_sns_topic.ops_alerts_topic.arn]

  tags = local.common_tags
}
