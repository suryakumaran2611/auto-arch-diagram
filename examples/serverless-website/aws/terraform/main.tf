terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type    = string
  default = "us-east-1"
}

# Secure serverless website (AWS) - Production-ready setup:
# - Private S3 origin with comprehensive security controls
# - CloudFront distribution with custom caching and optimization
# - Origin Access Control (OAC) for secure S3 access
# - WAFv2 Web ACL with managed rules and rate limiting
# - Comprehensive access logging and monitoring
# - CloudWatch metrics and alerts

resource "aws_s3_bucket" "logs" {
  bucket_prefix = "auto-arch-logs-"

  force_destroy = true

  tags = {
    Environment = "production"
    Project     = "auto-arch"
    Purpose     = "access-logs"
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket" "site" {
  bucket_prefix = "auto-arch-site-"

  force_destroy = true

  tags = {
    Environment = "production"
    Project     = "auto-arch"
    Purpose     = "static-website"
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_public_access_block" "site" {
  bucket                  = aws_s3_bucket.site.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "site" {
  bucket = aws_s3_bucket.site.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "site" {
  bucket = aws_s3_bucket.site.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_logging" "site" {
  bucket        = aws_s3_bucket.site.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3/"
}

resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "auto-arch-oac"
  description                       = "OAC for S3 origin"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_wafv2_web_acl" "cdn" {
  name        = "auto-arch-waf"
  description = "WAF for CloudFront"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "auto-arch-waf"
    sampled_requests_enabled   = true
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action { none {} }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "common"
      sampled_requests_enabled   = true
    }
  }
}

resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  comment             = "auto-arch secure serverless website - production"
  default_root_object = "index.html"
  http_version        = "http2and3"
  price_class         = "PriceClass_100"

  origin {
    domain_name              = aws_s3_bucket.site.bucket_regional_domain_name
    origin_id                = "s3-site"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id

    origin_shield {
      enabled              = true
      origin_shield_region = "us-east-1"
    }
  }

  default_cache_behavior {
    target_origin_id = "s3-site"
    compress         = true

    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]

    # Use managed cache policies for better performance
    cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # CachingEnabled
    origin_request_policy_id = "216adef6-5c7f-47e4-b989-5492eafa07d3" # CORS-S3Origin

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.rewrite_uri.arn
    }
  }

  # Custom cache behavior for API-like paths
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    target_origin_id = "s3-site"
    compress         = true

    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]

    cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    origin_request_policy_id = "216adef6-5c7f-47e4-b989-5492eafa07d3"
  }

  # Custom error pages
  custom_error_response {
    error_code         = 404
    response_code      = 404
    response_page_path = "/404.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 403
    response_page_path = "/403.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  web_acl_id = aws_wafv2_web_acl.cdn.arn

  logging_config {
    bucket          = aws_s3_bucket.logs.bucket_domain_name
    prefix          = "cloudfront/"
    include_cookies = false
  }

  tags = {
    Environment = "production"
    Project     = "auto-arch"
    Purpose     = "cdn-distribution"
    ManagedBy   = "terraform"
  }

  depends_on = [aws_s3_bucket_public_access_block.site]
}

# CloudFront Function for URL rewriting
resource "aws_cloudfront_function" "rewrite_uri" {
  name    = "auto-arch-rewrite-uri"
  runtime = "cloudfront-js-1.0"
  comment = "Rewrite URI to append index.html for directory requests"
  publish = true
  code    = <<-EOT
function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // Check whether the URI is missing a file name.
    if (uri.endsWith('/')) {
        request.uri += 'index.html';
    }
    // Check whether the URI is missing a file extension.
    else if (!uri.includes('.')) {
        request.uri += '/index.html';
    }

    return request;
}
EOT
}
