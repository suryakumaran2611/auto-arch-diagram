<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph AZURERM[AZURERM]
  tf_azurerm_cdn_endpoint_endpoint["azurerm_cdn_endpoint.endpoint"]
  tf_azurerm_cdn_profile_cdn["azurerm_cdn_profile.cdn"]
  tf_azurerm_resource_group_rg["azurerm_resource_group.rg"]
  tf_azurerm_storage_account_site["azurerm_storage_account.site"]
end
subgraph OTHER[OTHER]
  tf_random_string_suffix["random_string.suffix"]
end
tf_azurerm_cdn_profile_cdn --> tf_azurerm_cdn_endpoint_endpoint
tf_azurerm_resource_group_rg --> tf_azurerm_cdn_endpoint_endpoint
tf_azurerm_resource_group_rg --> tf_azurerm_cdn_profile_cdn
tf_azurerm_resource_group_rg --> tf_azurerm_storage_account_site
tf_azurerm_storage_account_site --> tf_azurerm_cdn_endpoint_endpoint
tf_random_string_suffix --> tf_azurerm_cdn_endpoint_endpoint
tf_random_string_suffix --> tf_azurerm_cdn_profile_cdn
tf_random_string_suffix --> tf_azurerm_resource_group_rg
tf_random_string_suffix --> tf_azurerm_storage_account_site
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact
