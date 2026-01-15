terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Secure serverless website (Azure) - simplified reference:
# - Storage Account (TLS1.2, HTTPS only, no public blob access)
# - CDN profile/endpoint (HTTPS only)

resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
}

resource "azurerm_resource_group" "rg" {
  name     = "rg-auto-arch-${random_string.suffix.result}"
  location = "eastus"
}

resource "azurerm_storage_account" "site" {
  name                     = "autoarch${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  min_tls_version           = "TLS1_2"
  enable_https_traffic_only = true
  allow_nested_items_to_be_public = false
}

resource "azurerm_cdn_profile" "cdn" {
  name                = "cdn-auto-arch-${random_string.suffix.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "Standard_Microsoft"
}

resource "azurerm_cdn_endpoint" "endpoint" {
  name                = "ep-auto-arch-${random_string.suffix.result}"
  profile_name        = azurerm_cdn_profile.cdn.name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  origin_host_header = "${azurerm_storage_account.site.name}.blob.core.windows.net"

  origin {
    name      = "storage"
    host_name = "${azurerm_storage_account.site.name}.blob.core.windows.net"
  }

  is_http_allowed  = false
  is_https_allowed = true

  depends_on = [azurerm_storage_account.site]
}
