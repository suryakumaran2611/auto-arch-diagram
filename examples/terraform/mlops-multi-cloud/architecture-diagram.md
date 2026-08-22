<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph all_AWS[AWS]
  subgraph vpc_aws_vpc_vpc_aws_network[VPC
vpc aws network]
    tf_aws_vpc_vpc_aws_network["aws_vpc.vpc_aws_network"]
    subgraph subnet_aws_subnet_subnet_aws_network[Subnet
subnet aws network (Private)]
      tf_aws_subnet_subnet_aws_network["aws_subnet.subnet_aws_network"]
    end
  end
  tf_aws_s3_bucket_s3_global["aws_s3_bucket.s3_global"]
end
subgraph all_Azure[Azure]
  tf_azurerm_resource_group_rg_azure_network["azurerm_resource_group.rg_azure_network"]
  tf_azurerm_storage_account_storage_global["azurerm_storage_account.storage_global"]
  tf_azurerm_storage_container_container_global["azurerm_storage_container.container_global"]
end
subgraph all_GCP[GCP]
  tf_google_storage_bucket_bucket_global["google_storage_bucket.bucket_global"]
end
tf_aws_vpc_vpc_aws_network --> tf_aws_subnet_subnet_aws_network
tf_azurerm_resource_group_rg_azure_network --> tf_azurerm_storage_account_storage_global
tf_azurerm_storage_account_storage_global --> tf_azurerm_storage_container_container_global
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact

## AI Architecture Insights

*Reviewed by OpenRouter free vision model `stealth/ox-alpha` (quality score: 6/10).*

Multi-cloud foundation spanning AWS, Azure, and GCP with no cross-provider integration yet.

- **AWS**: `vpc_aws_network` provides an isolated boundary containing private `subnet_aws_network`; `s3_global` stands alone as object storage.
- **Azure**: `rg_azure_network` scopes `storage_global`, whose account-level encryption protects blobs written to `container_global`.
- **GCP**: `bucket_global` is a third, independent object store.

The three stacks share zero edges — no peering, IAM trust, replication, or compute tier connects them. As rendered, this is scaffolding: network plus per-provider buckets awaiting workloads, pipelines, and identity wiring.

**Context hints**
- `[S3]` s3_global provides AWS object storage; global suffix implies cross-region access intent.
- `[NETWORK]` vpc_aws_network isolates AWS workloads; subnet_aws_network is private, blocking direct public ingress.
- `[DATA]` storage_global encrypts container_global objects with account-managed keys; container scopes blob writes.
- `[GENERAL]` rg_azure_network is deployment scope; edge parents storage_global despite network-oriented name.
- `[DATA]` bucket_global parallels s3_global on GCP; three disconnected object stores suggest staged multi-cloud strategy.
- `[GENERAL]` No compute consumes these stores yet; no producers, consumers, or replication edges exist.

**Contextual labels applied:** `s3_global` → Global Object Store, `vpc_aws_network` → Isolated Private Network, `subnet_aws_network` → Private Workload Subnet, `rg_azure_network` → Azure Deployment Scope, `storage_global` → Blob Storage Account, `bucket_global` → Global Object Bucket

**Review notes**
- [grouping] container_global separated from parent storage_global into an unrelated 'Containers' cluster.
- [grouping] rg_azure_network filed under 'Other' although it is the Azure scope parent of storage_global.
- [labeling] Captions duplicate raw name fragments ('s3 global', 'vpc aws network'); no functional or tag-based labels.
- [completeness] s3_global and bucket_global are edge-isolated; any inter-cloud relationships are unstated.
- [layout] Oversized empty band between Storage and Network clusters yields a tall, narrow canvas.

Feedback iterations: iter0: 6/10, iter1: 6/10, iter2: 6/10

**AI-refined diagram files** (include legend and review hints): architecture-diagram-ai.png, architecture-diagram-ai.jpg, architecture-diagram-ai.svg
