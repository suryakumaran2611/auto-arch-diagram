# Multi-Region Active-Passive Architecture (AWS)
# Demonstrates region-aware grouping in architecture diagrams.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "dr"
  region = "us-west-2"
}

# ---------- Primary Region: us-east-1 ----------
resource "aws_vpc" "primary" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name   = "primary-vpc"
    Region = "us-east-1"
  }
}

resource "aws_subnet" "primary_private_a" {
  vpc_id            = aws_vpc.primary.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "us-east-1a"
  tags = {
    Name = "primary-private-a"
    Tier = "private"
  }
}

resource "aws_security_group" "app_sg" {
  name   = "primary-app-sg"
  vpc_id = aws_vpc.primary.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "primary-app-sg"
  }
}

resource "aws_instance" "app_primary" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.primary_private_a.id
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  tags = {
    Name = "app-primary"
  }
}

resource "aws_db_subnet_group" "primary_db" {
  name       = "primary-db-subnet-group"
  subnet_ids = [aws_subnet.primary_private_a.id]
}

resource "aws_rds_cluster" "app_db_primary" {
  cluster_identifier   = "app-primary-cluster"
  engine               = "aurora-mysql"
  master_username      = "admin"
  master_password      = "ChangeMe123!"
  db_subnet_group_name = aws_db_subnet_group.primary_db.name
  skip_final_snapshot  = true
  tags = {
    Name = "app-db-primary"
  }
}

# ---------- DR Region: us-west-2 ----------
resource "aws_vpc" "dr" {
  provider   = aws.dr
  cidr_block = "10.1.0.0/16"
  tags = {
    Name   = "dr-vpc"
    Region = "us-west-2"
  }
}

resource "aws_subnet" "dr_private_a" {
  provider          = aws.dr
  vpc_id            = aws_vpc.dr.id
  cidr_block        = "10.1.10.0/24"
  availability_zone = "us-west-2a"
  tags = {
    Name = "dr-private-a"
    Tier = "private"
  }
}

resource "aws_instance" "app_dr" {
  provider               = aws.dr
  ami                    = "ami-084568db4383264d4"
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.dr_private_a.id
  vpc_security_group_ids = []
  tags = {
    Name = "app-dr"
  }
}

resource "aws_db_subnet_group" "dr_db" {
  provider   = aws.dr
  name       = "dr-db-subnet-group"
  subnet_ids = [aws_subnet.dr_private_a.id]
}

resource "aws_rds_cluster" "app_db_dr" {
  provider             = aws.dr
  cluster_identifier   = "app-dr-cluster"
  engine               = "aurora-mysql"
  master_username      = "admin"
  master_password      = "ChangeMe123!"
  db_subnet_group_name = aws_db_subnet_group.dr_db.name
  skip_final_snapshot  = true
  tags = {
    Name = "app-db-dr"
  }
}

# Cross-region topology connectors
resource "aws_vpc_peering_connection" "primary_to_dr" {
  vpc_id      = aws_vpc.primary.id
  peer_vpc_id = aws_vpc.dr.id
  peer_region = "us-west-2"
  auto_accept = false

  tags = {
    Name = "primary-to-dr"
  }
}

resource "aws_rds_cluster" "read_replica_link" {
  cluster_identifier              = "app-replica-link"
  engine                          = "aurora-mysql"
  master_username                 = "admin"
  master_password                 = "ChangeMe123!"
  replication_source_identifier   = aws_rds_cluster.app_db_primary.arn
  db_subnet_group_name            = aws_db_subnet_group.primary_db.name
  skip_final_snapshot             = true
  tags = {
    Name            = "cross-region-replica"
    secondary_region = "us-west-2"
  }
}
