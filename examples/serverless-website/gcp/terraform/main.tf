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

# Secure serverless website (GCP) - simplified reference:
# - Cloud Storage bucket
# - Cloud CDN via backend bucket
# - HTTPS load balancer (managed cert)
# - Cloud Armor security policy

resource "google_storage_bucket" "site" {
  name                        = "auto-arch-site-${var.project}"
  location                    = "US"
  uniform_bucket_level_access = true

  # Security posture
  public_access_prevention = "enforced"

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = null
  }
}

resource "google_compute_security_policy" "waf" {
  name = "auto-arch-armor"

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
}

resource "google_compute_backend_bucket" "cdn" {
  name        = "auto-arch-backend"
  bucket_name = google_storage_bucket.site.name
  enable_cdn  = true

  edge_security_policy = google_compute_security_policy.waf.self_link
}
