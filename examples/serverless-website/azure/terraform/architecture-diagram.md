<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
  subgraph all_Azure[Azure]
    tf_azurerm_cdn_endpoint_endpoint["azurerm_cdn_endpoint.endpoint"]
    tf_azurerm_cdn_frontdoor_firewall_policy_waf["azurerm_cdn_frontdoor_firewall_policy.waf"]
    tf_azurerm_cdn_profile_cdn["azurerm_cdn_profile.cdn"]
    tf_azurerm_resource_group_rg["azurerm_resource_group.rg"]
    tf_azurerm_storage_account_logs["azurerm_storage_account.logs"]
    tf_azurerm_storage_account_site["azurerm_storage_account.site"]
  end
tf_azurerm_cdn_profile_cdn --> tf_azurerm_cdn_endpoint_endpoint
tf_azurerm_resource_group_rg --> tf_azurerm_cdn_endpoint_endpoint
tf_azurerm_resource_group_rg --> tf_azurerm_cdn_frontdoor_firewall_policy_waf
tf_azurerm_resource_group_rg --> tf_azurerm_cdn_profile_cdn
tf_azurerm_resource_group_rg --> tf_azurerm_storage_account_logs
tf_azurerm_resource_group_rg --> tf_azurerm_storage_account_site
tf_azurerm_storage_account_site --> tf_azurerm_cdn_endpoint_endpoint
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact
