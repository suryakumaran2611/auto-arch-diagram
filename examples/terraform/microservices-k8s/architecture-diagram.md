<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph all_AWS[AWS]
  subgraph vpc_aws_vpc_main[VPC
main]
    tf_aws_vpc_main["aws_vpc.main"]
    subgraph subnet_aws_subnet_private[Subnet
private (Private)]
      tf_aws_subnet_private["aws_subnet.private"]
      tf_aws_db_instance_microservices["aws_db_instance.microservices"]
      tf_aws_db_subnet_group_microservices["aws_db_subnet_group.microservices"]
      subgraph cluster_aws_eks_cluster_main[EKS Cluster
main]
        tf_aws_eks_cluster_main["aws_eks_cluster.main"]
        tf_aws_eks_node_group_main["aws_eks_node_group.main"]
      end
      tf_aws_elasticache_cluster_microservices["aws_elasticache_cluster.microservices"]
      tf_aws_elasticache_subnet_group_microservices["aws_elasticache_subnet_group.microservices"]
      tf_aws_route_table_association_private["aws_route_table_association.private"]
    end
    subgraph subnet_aws_subnet_public[Subnet
public (Public)]
      tf_aws_subnet_public["aws_subnet.public"]
      tf_aws_nat_gateway_main["aws_nat_gateway.main"]
      tf_aws_route_table_association_public["aws_route_table_association.public"]
    end
    tf_aws_internet_gateway_main["aws_internet_gateway.main"]
    tf_aws_route_table_private["aws_route_table.private"]
    tf_aws_route_table_public["aws_route_table.public"]
    tf_aws_security_group_eks_cluster["aws_security_group.eks_cluster"]
    tf_aws_security_group_eks_nodes["aws_security_group.eks_nodes"]
    tf_aws_security_group_elasticache["aws_security_group.elasticache"]
    tf_aws_security_group_rds["aws_security_group.rds"]
  end
  tf_aws_cloudwatch_log_group_eks["aws_cloudwatch_log_group.eks"]
  tf_aws_ecr_repository_microservices["aws_ecr_repository.microservices"]
  tf_aws_eip_nat["aws_eip.nat"]
  tf_aws_iam_instance_profile_eks_nodes["aws_iam_instance_profile.eks_nodes"]
  tf_aws_iam_role_eks_cluster["aws_iam_role.eks_cluster"]
  tf_aws_iam_role_eks_nodes["aws_iam_role.eks_nodes"]
  tf_aws_iam_role_policy_attachment_eks_cluster_policy["aws_iam_role_policy_attachment.eks_cluster_policy"]
  tf_aws_iam_role_policy_attachment_eks_cni_policy["aws_iam_role_policy_attachment.eks_cni_policy"]
  tf_aws_iam_role_policy_attachment_eks_nodes_policy["aws_iam_role_policy_attachment.eks_nodes_policy"]
  tf_aws_iam_role_policy_attachment_eks_registry_policy["aws_iam_role_policy_attachment.eks_registry_policy"]
end
tf_aws_db_subnet_group_microservices --> tf_aws_db_instance_microservices
tf_aws_eip_nat --> tf_aws_nat_gateway_main
tf_aws_eks_cluster_main --> tf_aws_eks_node_group_main
tf_aws_elasticache_subnet_group_microservices --> tf_aws_elasticache_cluster_microservices
tf_aws_iam_role_eks_cluster --> tf_aws_eks_cluster_main
tf_aws_iam_role_eks_cluster --> tf_aws_iam_role_policy_attachment_eks_cluster_policy
tf_aws_iam_role_eks_nodes --> tf_aws_eks_node_group_main
tf_aws_iam_role_eks_nodes --> tf_aws_iam_instance_profile_eks_nodes
tf_aws_iam_role_eks_nodes --> tf_aws_iam_role_policy_attachment_eks_cni_policy
tf_aws_iam_role_eks_nodes --> tf_aws_iam_role_policy_attachment_eks_nodes_policy
tf_aws_iam_role_eks_nodes --> tf_aws_iam_role_policy_attachment_eks_registry_policy
tf_aws_iam_role_policy_attachment_eks_cluster_policy --> tf_aws_eks_cluster_main
tf_aws_iam_role_policy_attachment_eks_cni_policy --> tf_aws_eks_node_group_main
tf_aws_iam_role_policy_attachment_eks_nodes_policy --> tf_aws_eks_node_group_main
tf_aws_iam_role_policy_attachment_eks_registry_policy --> tf_aws_eks_node_group_main
tf_aws_internet_gateway_main --> tf_aws_eip_nat
tf_aws_internet_gateway_main --> tf_aws_nat_gateway_main
tf_aws_internet_gateway_main --> tf_aws_route_table_public
tf_aws_nat_gateway_main --> tf_aws_route_table_private
tf_aws_route_table_private --> tf_aws_route_table_association_private
tf_aws_route_table_public --> tf_aws_route_table_association_public
tf_aws_security_group_eks_cluster --> tf_aws_eks_cluster_main
tf_aws_security_group_eks_cluster --> tf_aws_security_group_eks_nodes
tf_aws_security_group_eks_nodes --> tf_aws_security_group_elasticache
tf_aws_security_group_eks_nodes --> tf_aws_security_group_rds
tf_aws_security_group_elasticache --> tf_aws_elasticache_cluster_microservices
tf_aws_security_group_rds --> tf_aws_db_instance_microservices
tf_aws_subnet_private --> tf_aws_db_subnet_group_microservices
tf_aws_subnet_private --> tf_aws_eks_cluster_main
tf_aws_subnet_private --> tf_aws_eks_node_group_main
tf_aws_subnet_private --> tf_aws_elasticache_subnet_group_microservices
tf_aws_subnet_private --> tf_aws_route_table_association_private
tf_aws_subnet_public --> tf_aws_nat_gateway_main
tf_aws_subnet_public --> tf_aws_route_table_association_public
tf_aws_vpc_main --> tf_aws_internet_gateway_main
tf_aws_vpc_main --> tf_aws_route_table_private
tf_aws_vpc_main --> tf_aws_route_table_public
tf_aws_vpc_main --> tf_aws_security_group_eks_cluster
tf_aws_vpc_main --> tf_aws_security_group_eks_nodes
tf_aws_vpc_main --> tf_aws_security_group_elasticache
tf_aws_vpc_main --> tf_aws_security_group_rds
tf_aws_vpc_main --> tf_aws_subnet_private
tf_aws_vpc_main --> tf_aws_subnet_public
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact

## AI Architecture Insights

*Reviewed by OpenRouter free vision model `stealth/ox-alpha` (quality score: 4/10).*

**End-to-end:** Terraform provisions `vpc_main` split into public/private subnets. `internet_gateway_main` handles public ingress; `nat_gateway_main` with `eip_nat` grants private subnets outbound-only access. `eks_cluster_main` controls `eks_node_group_main`, whose nodes assume `iam_role_eks_nodes` (CNI, worker, registry policies) and pull images from `ecr_repository_microservices`. Pod traffic reaches `db_instance_microservices` (relational state) and `elasticache_cluster_microservices` (cache tier) only through chained security groups: `eks_cluster` → `eks_nodes` → `rds` / `elasticache`. Subnet groups pin both data stores into private subnets; logs flow to `cloudwatch_log_group_eks`.

**Context hints**
- `[COMPUTE]` eks_node_group_main runs containerized microservices in private subnets via NAT egress.
- `[DATA]` db_instance_microservices stores relational state; reachable only through security_group_rds.
- `[DATA]` elasticache_cluster_microservices caches hot data for pods; guarded by security_group_elasticache.
- `[IAM]` iam_role_eks_nodes grants nodes CloudWatch logging and ECR pull via attached policies.
- `[NETWORK]` nat_gateway_main plus eip_nat give private subnets outbound-only internet access.
- `[GENERAL]` ecr_repository_microservices supplies container images pulled by eks_node_group_main.

**Contextual labels applied:** `eks_cluster_main` → EKS Control Plane, `eks_node_group_main` → Worker Nodes (Private), `db_instance_microservices` → Primary Relational Database, `elasticache_cluster_microservices` → Redis Cache Tier, `nat_gateway_main` → Outbound NAT Gateway, `ecr_repository_microservices` → Microservice Image Registry (+2 more)

**Review notes**
- [labeling] Truncated labels: 'Route Table...', 'IAM Role Policy...', 'Elastiache Subnet...' obscure resource identity.
- [edge-routing] Red dashed IAM/security-group edges cross the full canvas, overlapping every cluster.
- [layout] Security cluster placed far above Network, forcing dozens of long vertical edges.
- [grouping] 'Other' mixes unrelated concerns: EIP belongs beside NAT gateway, not with logs/registry.
- [completeness] Data-plane flows (pods→RDS/ElastiCache/ECR) absent; only infrastructure wiring is drawn.

Feedback iterations: iter0: 4/10, iter1: 4/10, iter2: 4/10

**AI-refined diagram files** (include legend and review hints): architecture-diagram-ai.png, architecture-diagram-ai.jpg, architecture-diagram-ai.svg
