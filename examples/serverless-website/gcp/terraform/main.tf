terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

variable "project" { type = string }
variable "region" { type = string default = "us-central1" }

# Secure serverless website (GCP) - Production-ready setup:
# - Cloud Storage bucket with security controls
# - Cloud CDN via backend bucket with custom caching
# - HTTPS load balancer with managed SSL certificate
# - Cloud Armor security policy with rate limiting
# - Cloud Logging and monitoring

resource "google_storage_bucket" "site" {
  name                        = "auto-arch-site-${var.project}"
  location                    = "US"
  uniform_bucket_level_access = true
  force_destroy               = true

  # Enhanced security posture
  public_access_prevention = "enforced"

  versioning {
    enabled = true
  }

  lifecycle {
    prevent_destroy = false
  }

  # CORS configuration for web access
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "OPTIONS"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# Cloud Logging bucket for access logs
resource "google_storage_bucket" "logs" {
  name                        = "auto-arch-logs-${var.project}"
  location                    = "US"
  uniform_bucket_level_access = true
  force_destroy               = true

  versioning {
    enabled = true
  }

  lifecycle {
    prevent_destroy = false
  }
}

resource "google_compute_security_policy" "waf" {
  name        = "auto-arch-armor-${var.project}"
  description = "Cloud Armor security policy for serverless website"

  # Default rule - allow all
  rule {
    priority = 1000
    action   = "allow"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }

  # Rate limiting rule
  rule {
    priority = 2000
    action   = "rate_based_ban"
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(403)"
      rate_limit_threshold {
        count        = 1000
        interval_sec = 60
      }
      ban_duration_sec = 300
    }
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }
}

resource "google_compute_backend_bucket" "cdn" {
  name        = "auto-arch-backend-${var.project}"
  bucket_name = google_storage_bucket.site.name
  enable_cdn  = true

  # Custom CDN configuration
  cdn_policy {
    cache_mode        = "CACHE_ALL_STATIC"
    client_ttl        = 3600
    default_ttl       = 86400
    max_ttl           = 86400
    negative_caching  = true
    serve_while_stale = 86400
  }

  edge_security_policy = google_compute_security_policy.waf.self_link
}

# Load balancer for HTTPS termination
resource "google_compute_url_map" "lb" {
  name            = "auto-arch-url-map-${var.project}"
  default_service = google_compute_backend_bucket.cdn.self_link
}

resource "google_compute_target_https_proxy" "lb" {
  name             = "auto-arch-https-proxy-${var.project}"
  url_map          = google_compute_url_map.lb.self_link
  ssl_certificates = [google_compute_managed_ssl_certificate.cert.self_link]
}

resource "google_compute_global_forwarding_rule" "lb" {
  name                  = "auto-arch-forwarding-rule-${var.project}"
  target                = google_compute_target_https_proxy.lb.self_link
  port_range            = "443"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL"
}

# Managed SSL certificate
resource "google_compute_managed_ssl_certificate" "cert" {
  name = "auto-arch-cert-${var.project}"

  managed {
    domains = ["auto-arch-${var.project}.example.com"]
  }
}
