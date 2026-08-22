<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph all_AWS[AWS]
  subgraph vpc_aws_vpc_peer[VPC
peer]
    tf_aws_vpc_peer["aws_vpc.peer"]
    subgraph subnet_aws_subnet_peer_private[Subnet
peer private (Private)]
      tf_aws_subnet_peer_private["aws_subnet.peer_private"]
      tf_aws_instance_peer_app["aws_instance.peer_app"]
      tf_aws_route_table_association_peer_private_assoc["aws_route_table_association.peer_private_assoc"]
    end
    subgraph subnet_aws_subnet_peer_public[Subnet
peer public (Public)]
      tf_aws_subnet_peer_public["aws_subnet.peer_public"]
    end
  end
  subgraph vpc_aws_vpc_primary[VPC
primary]
    tf_aws_vpc_primary["aws_vpc.primary"]
    subgraph subnet_aws_subnet_primary_private[Subnet
primary private (Private)]
      tf_aws_subnet_primary_private["aws_subnet.primary_private"]
      tf_aws_instance_primary_app["aws_instance.primary_app"]
      tf_aws_route_table_association_primary_private_assoc["aws_route_table_association.primary_private_assoc"]
    end
    subgraph subnet_aws_subnet_primary_public[Subnet
primary public (Public)]
      tf_aws_subnet_primary_public["aws_subnet.primary_public"]
    end
  end
  tf_aws_route_table_peer_rt["aws_route_table.peer_rt"]
  tf_aws_route_table_primary_rt["aws_route_table.primary_rt"]
  tf_aws_security_group_peer_app["aws_security_group.peer_app"]
  tf_aws_security_group_primary_app["aws_security_group.primary_app"]
  tf_aws_vpc_peering_connection_primary_to_peer["aws_vpc_peering_connection.primary_to_peer"]
end
tf_aws_route_table_peer_rt --> tf_aws_route_table_association_peer_private_assoc
tf_aws_route_table_primary_rt --> tf_aws_route_table_association_primary_private_assoc
tf_aws_security_group_peer_app --> tf_aws_instance_peer_app
tf_aws_security_group_primary_app --> tf_aws_instance_primary_app
tf_aws_subnet_peer_private --> tf_aws_instance_peer_app
tf_aws_subnet_peer_private --> tf_aws_route_table_association_peer_private_assoc
tf_aws_subnet_primary_private --> tf_aws_instance_primary_app
tf_aws_subnet_primary_private --> tf_aws_route_table_association_primary_private_assoc
tf_aws_vpc_peer --> tf_aws_route_table_peer_rt
tf_aws_vpc_peer --> tf_aws_route_table_primary_rt
tf_aws_vpc_peer --> tf_aws_security_group_peer_app
tf_aws_vpc_peer --> tf_aws_security_group_primary_app
tf_aws_vpc_peer --> tf_aws_subnet_peer_private
tf_aws_vpc_peer --> tf_aws_subnet_peer_public
tf_aws_vpc_peer --> tf_aws_vpc_peering_connection_primary_to_peer
tf_aws_vpc_peering_connection_primary_to_peer --> tf_aws_route_table_peer_rt
tf_aws_vpc_peering_connection_primary_to_peer --> tf_aws_route_table_primary_rt
tf_aws_vpc_primary --> tf_aws_route_table_peer_rt
tf_aws_vpc_primary --> tf_aws_route_table_primary_rt
tf_aws_vpc_primary --> tf_aws_security_group_peer_app
tf_aws_vpc_primary --> tf_aws_security_group_primary_app
tf_aws_vpc_primary --> tf_aws_subnet_primary_private
tf_aws_vpc_primary --> tf_aws_subnet_primary_public
tf_aws_vpc_primary --> tf_aws_vpc_peering_connection_primary_to_peer
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact

## AI Architecture Insights

*Reviewed by OpenRouter free vision model `stealth/ox-alpha` (quality score: 5/10).*

**End-to-end:** Two VPCs (`primary`, `peer`) are joined by `aws_vpc_peering_connection.primary_to_peer`. Each VPC has one public and one private subnet; both app EC2 instances (`primary_app`, `peer_app`) sit in **private** subnets, so all compute is non-internet-facing. Private-subnet route table associations (`primary_private_assoc`, `peer_private_assoc`) bind `primary_rt`/`peer_rt` to those subnets, and both route tables reference the peering connection for cross-VPC routing. Per-app security groups (`primary_app`, `peer_app`) are scoped per VPC and attached to their instances, gating east-west traffic over the peering link. Public subnets are provisioned but idle.

**Context hints**
- `[NETWORK]` Peering primary_to_peer routes traffic privately between primary and peer VPCs.
- `[COMPUTE]` Instance primary_app runs inside primary_private subnet, isolated from internet.
- `[COMPUTE]` Instance peer_app runs inside peer_private subnet of peer VPC.
- `[IAM]` Security groups primary_app and peer_app filter traffic to their instances.
- `[NETWORK]` Route tables primary_rt and peer_rt attach only to private subnets.
- `[NETWORK]` Subnets primary_public and peer_public currently host no compute workloads.

**Contextual labels applied:** `primary_app` → Primary App Server, `peer_app` → Peer App Server, `primary_to_peer` → Cross-VPC Peering Link, `primary_private` → Primary Private Subnet, `peer_private` → Peer Private Subnet, `primary_app_sg` → Primary App Firewall (+1 more)

**Review notes**
- [layout] Extreme vertical stretch; Security cluster pushed far below forces very long dashed edges.
- [labeling] Truncated labels: 'Route Table...', 'VPC Peering...', 'primary private...' unreadable.
- [edge-routing] Red dashed security-group edges span full canvas height, crossing all network clusters.
- [grouping] Route table associations render as stacked CIDR chips, obscuring node identity.
- [edge-routing] Multiple parallel VPC-to-route-table edges create dense crossings near peering node.

Feedback iterations: iter0: 4/10, iter1: 5/10, iter2: 5/10, iter3: 4/10

**AI-refined diagram files** (include legend and review hints): architecture-diagram-ai.png, architecture-diagram-ai.jpg, architecture-diagram-ai.svg
