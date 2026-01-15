terraform {
  required_version = ">= 1.5.0"
  required_providers {
    ibm = {
      source  = "IBM-Cloud/ibm"
      version = ">= 1.60.0"
    }
  }
}

# Secure serverless website (IBM Cloud) - simplified reference:
# - Cloud Object Storage bucket
# - (Optional) IBM Cloud Internet Services (CIS) for CDN/WAF/TLS

variable "ibmcloud_api_key" { type = string }
variable "region" { type = string default = "us-south" }

provider "ibm" {
  ibmcloud_api_key = var.ibmcloud_api_key
  region           = var.region
}

resource "ibm_resource_instance" "cos" {
  name     = "auto-arch-cos"
  service  = "cloud-object-storage"
  plan     = "standard"
  location = "global"
}

resource "ibm_cos_bucket" "site" {
  bucket_name          = "auto-arch-site"
  resource_instance_id = ibm_resource_instance.cos.id
  region_location      = var.region

  # Security posture
  hard_quota = 1024
}
