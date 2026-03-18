# AWS VPC Peering Example - Multi-Subnet Architecture
# Demonstrates two VPCs with public/private subnets and VPC peering.

terraform {
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

# Primary VPC
resource "aws_vpc" "primary" {
  cidr_block           = "10.10.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "primary-vpc"
  }
}

# Peer VPC
resource "aws_vpc" "peer" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "peer-vpc"
  }
}

# Primary VPC subnets
resource "aws_subnet" "primary_public" {
  vpc_id                  = aws_vpc.primary.id
  cidr_block              = "10.10.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "primary-public-subnet"
    Tier = "public"
  }
}

resource "aws_subnet" "primary_private" {
  vpc_id            = aws_vpc.primary.id
  cidr_block        = "10.10.10.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "primary-private-subnet"
    Tier = "private"
  }
}

# Peer VPC subnets
resource "aws_subnet" "peer_public" {
  vpc_id                  = aws_vpc.peer.id
  cidr_block              = "10.20.1.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "peer-public-subnet"
    Tier = "public"
  }
}

resource "aws_subnet" "peer_private" {
  vpc_id            = aws_vpc.peer.id
  cidr_block        = "10.20.10.0/24"
  availability_zone = "us-east-1b"

  tags = {
    Name = "peer-private-subnet"
    Tier = "private"
  }
}

# VPC peering between primary and peer VPCs
resource "aws_vpc_peering_connection" "primary_to_peer" {
  vpc_id      = aws_vpc.primary.id
  peer_vpc_id = aws_vpc.peer.id
  auto_accept = true

  tags = {
    Name = "primary-to-peer-peering"
  }
}

# Route table resources to represent peering data path
resource "aws_route_table" "primary_rt" {
  vpc_id = aws_vpc.primary.id

  route {
    cidr_block                = aws_vpc.peer.cidr_block
    vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_peer.id
  }

  tags = {
    Name = "primary-rt"
  }
}

resource "aws_route_table" "peer_rt" {
  vpc_id = aws_vpc.peer.id

  route {
    cidr_block                = aws_vpc.primary.cidr_block
    vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_peer.id
  }

  tags = {
    Name = "peer-rt"
  }
}

resource "aws_route_table_association" "primary_private_assoc" {
  subnet_id      = aws_subnet.primary_private.id
  route_table_id = aws_route_table.primary_rt.id
}

resource "aws_route_table_association" "peer_private_assoc" {
  subnet_id      = aws_subnet.peer_private.id
  route_table_id = aws_route_table.peer_rt.id
}

# Example workloads in private subnets
resource "aws_security_group" "primary_app" {
  name   = "primary-app-sg"
  vpc_id = aws_vpc.primary.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.peer.cidr_block]
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

resource "aws_security_group" "peer_app" {
  name   = "peer-app-sg"
  vpc_id = aws_vpc.peer.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.primary.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "peer-app-sg"
  }
}

resource "aws_instance" "primary_app" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.primary_private.id
  vpc_security_group_ids = [aws_security_group.primary_app.id]

  tags = {
    Name = "primary-app"
  }
}

resource "aws_instance" "peer_app" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.peer_private.id
  vpc_security_group_ids = [aws_security_group.peer_app.id]

  tags = {
    Name = "peer-app"
  }
}
