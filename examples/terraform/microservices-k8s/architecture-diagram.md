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
    tf_aws_security_group_eks_cluster["aws_security_group.eks_cluster"]
  end
  tf_aws_cloudwatch_log_group_eks["aws_cloudwatch_log_group.eks"]
  tf_aws_ecr_repository_microservices["aws_ecr_repository.microservices"]
  tf_aws_eip_nat["aws_eip.nat"]
  subgraph cluster_aws_eks_cluster_main[EKS Cluster
main]
    tf_aws_eks_cluster_main["aws_eks_cluster.main"]
    tf_aws_eks_node_group_main["aws_eks_node_group.main"]
  end
  tf_aws_iam_instance_profile_eks_nodes["aws_iam_instance_profile.eks_nodes"]
  tf_aws_iam_role_eks_cluster["aws_iam_role.eks_cluster"]
  tf_aws_iam_role_eks_nodes["aws_iam_role.eks_nodes"]
  tf_aws_iam_role_policy_attachment_eks_cluster_policy["aws_iam_role_policy_attachment.eks_cluster_policy"]
  tf_aws_iam_role_policy_attachment_eks_cni_policy["aws_iam_role_policy_attachment.eks_cni_policy"]
  tf_aws_iam_role_policy_attachment_eks_nodes_policy["aws_iam_role_policy_attachment.eks_nodes_policy"]
  tf_aws_iam_role_policy_attachment_eks_registry_policy["aws_iam_role_policy_attachment.eks_registry_policy"]
  tf_aws_internet_gateway_main["aws_internet_gateway.main"]
  tf_aws_route_table_private["aws_route_table.private"]
  tf_aws_route_table_public["aws_route_table.public"]
  tf_aws_security_group_eks_nodes["aws_security_group.eks_nodes"]
  tf_aws_security_group_elasticache["aws_security_group.elasticache"]
  tf_aws_security_group_rds["aws_security_group.rds"]
end
tf_aws_db_subnet_group_microservices --> tf_aws_db_instance_microservices
tf_aws_eip_nat --> tf_aws_nat_gateway_main
tf_aws_eks_cluster_main --> tf_aws_eks_node_group_main
tf_aws_elasticache_subnet_group_microservices --> tf_aws_elasticache_cluster_microservices
tf_aws_iam_role_eks_cluster --> tf_aws_eks_cluster_main
tf_aws_iam_role_eks_cluster --> tf_aws_iam_role_policy_attachment_eks_cluster_policy
tf_aws_internet_gateway_main --> tf_aws_eip_nat
tf_aws_internet_gateway_main --> tf_aws_nat_gateway_main
tf_aws_security_group_rds --> tf_aws_db_instance_microservices
tf_aws_subnet_private --> tf_aws_db_subnet_group_microservices
tf_aws_vpc_main --> tf_aws_security_group_eks_cluster
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact

## AI Architecture Insights

*Reviewed by OpenRouter free vision model `stealth/ox-alpha` (quality score: 5/10).*

**Architecture:** Terraform-defined AWS platform pairing an EKS cluster and managed node group with RDS and ElastiCache inside a two-tier VPC. Public subnets host only the NAT gateway; databases, cache, and Kubernetes workloads stay private.

**Dataflow:** Images publish to ECR → nodes pull via registry role → services persist to RDS through the DB subnet group and cache hot reads in ElastiCache; egress flows private subnet → NAT → internet gateway.

**Security:** Least-privilege security-group chaining (nodes→RDS/cache), separated cluster/node IAM roles, CloudWatch control-plane logging. Gaps: no KMS keys, no Secrets Manager, undefined log retention, no TLS/WAF ingress.

**Scaling:** Node group scales horizontally; RDS and Redis scale vertically—add read replicas, Multi-AZ, and Redis cluster mode for growth.

**Context hints**
- `[NETWORK]` Two-tier VPC isolates data tier; NAT gateway controls private-subnet egress.
- `[COMPUTE]` EKS cluster and managed node group operate entirely within private subnets.
- `[DATA]` RDS and ElastiCache colocated privately; no KMS or backup resources declared.
- `[IAM]` Separate least-privilege roles attach cluster, node, CNI, and registry policies.
- `[GENERAL]` CloudWatch log group captures control-plane activity; retention policy unspecified.
- `[SECRETS]` No secrets manager declared; database credential provisioning remains unaddressed.

**Contextual labels applied:** `eks_cluster` → Managed Kubernetes Control Plane, `eks_node_group` → Autoscaling Worker Fleet, `db_instance` → Primary Managed Database, `elasticache_cluster` → In-Memory Cache Tier, `nat_gateway` → Private Subnet Egress, `internet_gateway` → Public Ingress Gateway (+6 more)

**Review notes**
- [completeness] Eight declared resources missing from render: both route tables, both route table associations, four IAM role policy attachments, and the IAM instance profile.
- [grouping] Duplicate 'VPC main' node rendered outside its own subgraph while eks_cluster/eks_nodes security groups sit outside the VPC boundary they belong to.
- [labeling] Truncated label 'Elasticache Subnet...' obscures the resource identity.
- [edge-routing] Red dashed security edges span nearly the full canvas height, crossing multiple clusters and overlapping node icons.
- [layout] Extreme vertical aspect ratio: LR source direction collapses into a tall single column, hurting readability and print fit.

Feedback iterations: iter0: 5/10

**AI-refined diagram files** (include legend and review hints): architecture-diagram-ai.png, architecture-diagram-ai.jpg, architecture-diagram-ai.svg, architecture-diagram-ai.html, architecture-diagram-ai.drawio
