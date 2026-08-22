<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph all_AWS[AWS]
  subgraph vpc_aws_vpc_dr[VPC
dr]
    tf_aws_vpc_dr["aws_vpc.dr"]
    subgraph subnet_aws_subnet_dr_private_a[Subnet
dr private a (Private)]
      tf_aws_subnet_dr_private_a["aws_subnet.dr_private_a"]
      tf_aws_db_subnet_group_dr_db["aws_db_subnet_group.dr_db"]
      tf_aws_instance_app_dr["aws_instance.app_dr"]
      tf_aws_rds_cluster_app_db_dr["aws_rds_cluster.app_db_dr"]
    end
  end
  subgraph vpc_aws_vpc_primary[VPC
primary]
    tf_aws_vpc_primary["aws_vpc.primary"]
    subgraph subnet_aws_subnet_primary_private_a[Subnet
primary private a (Private)]
      tf_aws_subnet_primary_private_a["aws_subnet.primary_private_a"]
      tf_aws_db_subnet_group_primary_db["aws_db_subnet_group.primary_db"]
      tf_aws_instance_app_primary["aws_instance.app_primary"]
      tf_aws_rds_cluster_app_db_primary["aws_rds_cluster.app_db_primary"]
      tf_aws_rds_cluster_read_replica_link["aws_rds_cluster.read_replica_link"]
    end
    tf_aws_security_group_app_sg["aws_security_group.app_sg"]
  end
  tf_aws_vpc_peering_connection_primary_to_dr["aws_vpc_peering_connection.primary_to_dr"]
end
tf_aws_db_subnet_group_dr_db --> tf_aws_rds_cluster_app_db_dr
tf_aws_db_subnet_group_primary_db --> tf_aws_rds_cluster_app_db_primary
tf_aws_db_subnet_group_primary_db --> tf_aws_rds_cluster_read_replica_link
tf_aws_rds_cluster_app_db_primary --> tf_aws_rds_cluster_read_replica_link
tf_aws_security_group_app_sg --> tf_aws_instance_app_primary
tf_aws_subnet_dr_private_a --> tf_aws_db_subnet_group_dr_db
tf_aws_subnet_dr_private_a --> tf_aws_instance_app_dr
tf_aws_subnet_primary_private_a --> tf_aws_db_subnet_group_primary_db
tf_aws_subnet_primary_private_a --> tf_aws_instance_app_primary
tf_aws_vpc_dr --> tf_aws_subnet_dr_private_a
tf_aws_vpc_dr --> tf_aws_vpc_peering_connection_primary_to_dr
tf_aws_vpc_primary --> tf_aws_security_group_app_sg
tf_aws_vpc_primary --> tf_aws_subnet_primary_private_a
tf_aws_vpc_primary --> tf_aws_vpc_peering_connection_primary_to_dr
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact

## AI Architecture Insights

*Reviewed by OpenRouter free vision model `stealth/ox-alpha` (quality score: 6/10).*

**Multi-region HA web stack.** Each region runs a private-subnet EC2 app tier (`app_primary`, `app_dr`) backed by an Aurora cluster (`app_db_primary`, `app_db_dr`) placed via db subnet groups. `read_replica_link` streams changes from the primary writer to the DR cluster, keeping `app_db_dr` promotable during regional failure. `primary_to_dr` VPC peering provides the private path for replication and administrative traffic. `app_sg` gates inbound access to the primary instance only; the DR side currently relies on subnet isolation alone.

**Context hints**
- `[COMPUTE]` app_primary serves primary traffic; app_dr is warm standby in us-west-2
- `[DATA]` app_db_primary writes; app_db_dr receives cross-region replication via read_replica_link
- `[NETWORK]` primary_to_dr enables private inter-VPC routing for replication and failover traffic
- `[NETWORK]` app_sg restricts ingress to app_primary; app_dr has no security group
- `[DATA]` db subnet groups anchor each cluster to private subnets per VPC

**Contextual labels applied:** `app_primary` → Primary App Server, `app_dr` → Standby App Server, `app_db_primary` → Primary Aurora Writer, `app_db_dr` → Cross-Region Replica, `read_replica_link` → Aurora Replication Link, `primary_to_dr` → Inter-Region Peering

**Review notes**
- [layout] read_replica_link node drawn inside primary_private_a subnet despite spanning both regions
- [labeling] VPC peering label truncated to 'VPC Peering...' hiding target name
- [edge-routing] Dashed red VPC-to-SG-to-instance edges loop outside containers and overlap subnet border
- [grouping] Peering connection nested solely under us-west-2 though it belongs to both VPCs
- [completeness] No security-group edge shown for app_dr, leaving DR ingress posture ambiguous

Feedback iterations: iter0: 6/10, iter1: 6/10, iter2: 6/10

**AI-refined diagram files** (include legend and review hints): architecture-diagram-ai.png, architecture-diagram-ai.jpg, architecture-diagram-ai.svg
