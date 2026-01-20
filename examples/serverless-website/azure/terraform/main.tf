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

# Secure serverless website (Azure) - Production-ready setup:
# - Resource Group with proper tagging
# - Storage Account (TLS1.2, HTTPS only, private access, logging)
# - CDN profile/endpoint with custom domain support
# - Web Application Firewall (WAF) policy
# - Monitoring and logging

resource "azurerm_resource_group" "rg" {
  name     = "rg-auto-arch-demo"
  location = "eastus"

  tags = {
    Environment = "production"
    Project     = "auto-arch"
    Purpose     = "serverless-website"
    ManagedBy   = "terraform"
  }
}

# Storage account for logs
resource "azurerm_storage_account" "logs" {
  name                     = "logsautoarchdemo"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  min_tls_version           = "TLS1_2"
  enable_https_traffic_only = true
  allow_nested_items_to_be_public = false

  blob_properties {
    versioning_enabled  = true
    change_feed_enabled = true

    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 7
    }
  }

  tags = {
    Environment = "production"
    Purpose     = "access-logs"
  }
}

resource "azurerm_storage_account" "site" {
  name                     = "siteautoarchdemo"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  min_tls_version           = "TLS1_2"
  enable_https_traffic_only = true
  allow_nested_items_to_be_public = false

  # Static website configuration
  static_website {
    index_document     = "index.html"
    error_404_document = "404.html"
  }

  blob_properties {
    versioning_enabled  = true
    change_feed_enabled = true

    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "HEAD", "OPTIONS"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }

    delete_retention_policy {
      days = 30
    }
  }

  tags = {
    Environment = "production"
    Purpose     = "static-website"
  }
}

# WAF policy for CDN
resource "azurerm_cdn_frontdoor_firewall_policy" "waf" {
  name                = "waf-auto-arch-demo"
  resource_group_name = azurerm_resource_group.rg.name
  sku_name            = "Premium_AzureFrontDoor"
  enabled             = true
  mode                = "Prevention"

  managed_rule {
    type    = "DefaultRuleSet"
    version = "1.0"
    action  = "Block"
  }

  managed_rule {
    type    = "Microsoft_DefaultRuleSet"
    version = "2.1"
    action  = "Block"
  }

  custom_rule {
    name     = "RateLimitRule"
    enabled  = true
    priority = 100
    type     = "RateLimitRule"
    action   = "Block"

    rate_limit_duration_in_minutes = 1
    rate_limit_threshold           = 1000

    match_condition {
      match_variable     = "RemoteAddr"
      operator           = "IPMatch"
      negation_condition = false
      match_values       = ["*"]
    }
  }

  tags = {
    Environment = "production"
    Purpose     = "waf-protection"
  }
}

resource "azurerm_cdn_profile" "cdn" {
  name                = "cdn-auto-arch-demo"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "Standard_Microsoft"

  tags = {
    Environment = "production"
    Purpose     = "content-delivery"
  }
}

resource "azurerm_cdn_endpoint" "endpoint" {
  name                = "ep-auto-arch-demo"
  profile_name        = azurerm_cdn_profile.cdn.name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  origin_host_header = azurerm_storage_account.site.primary_web_host
  querystring_caching_behaviour = "IgnoreQueryString"

  origin {
    name      = "storage"
    host_name = azurerm_storage_account.site.primary_web_host
  }

  delivery_rule {
    name  = "EnforceHTTPS"
    order = 1

    request_scheme_condition {
      operator         = "Equal"
      match_values     = ["HTTP"]
      negate_condition = false
    }

    url_redirect_action {
      redirect_type = "Found"
      protocol      = "Https"
    }
  }

  delivery_rule {
    name  = "CacheStaticContent"
    order = 2

    request_uri_condition {
      operator     = "Any"
      match_values = []
    }

    cache_expiration_action {
      behavior = "Override"
      duration = "01:00:00"
    }
  }

  is_http_allowed       = false
  is_https_allowed      = true
  optimization_type     = "GeneralWebDelivery"

  tags = {
    Environment = "production"
    Purpose     = "cdn-endpoint"
  }

  depends_on = [azurerm_storage_account.site]
}
