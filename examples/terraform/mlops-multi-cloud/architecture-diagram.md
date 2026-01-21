<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph AWS[AWS]
  tf_aws_s3_bucket_s3_global["aws_s3_bucket.s3_global"]
  tf_aws_subnet_subnet_aws_network["aws_subnet.subnet_aws_network"]
  tf_aws_vpc_vpc_aws_network["aws_vpc.vpc_aws_network"]
end
subgraph Azure[Azure]
  tf_azurerm_resource_group_rg_azure_network["azurerm_resource_group.rg_azure_network"]
  tf_azurerm_storage_account_storage_global["azurerm_storage_account.storage_global"]
  tf_azurerm_storage_container_container_global["azurerm_storage_container.container_global"]
end
subgraph GCP[GCP]
  tf_google_storage_bucket_bucket_global["google_storage_bucket.bucket_global"]
end
tf_aws_vpc_vpc_aws_network --> tf_aws_subnet_subnet_aws_network
tf_azurerm_resource_group_rg_azure_network --> tf_azurerm_storage_account_storage_global
tf_azurerm_storage_account_storage_global --> tf_azurerm_storage_container_container_global
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact
