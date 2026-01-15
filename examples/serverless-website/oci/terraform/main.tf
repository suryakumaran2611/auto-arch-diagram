terraform {
  required_version = ">= 1.5.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0"
    }
  }
}

# Secure serverless website (OCI) - simplified reference:
# - Object Storage bucket
# - (Optional) OCI WAF / CDN in front of the bucket

variable "tenancy_ocid" { type = string }
variable "user_ocid" { type = string }
variable "fingerprint" { type = string }
variable "private_key_path" { type = string }
variable "region" { type = string }
variable "compartment_ocid" { type = string }

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

resource "oci_objectstorage_bucket" "site" {
  compartment_id = var.compartment_ocid
  name           = "auto-arch-site"
  namespace      = data.oci_objectstorage_namespace.ns.namespace

  access_type = "NoPublicAccess"
  versioning  = "Enabled"
}

data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.compartment_ocid
}
