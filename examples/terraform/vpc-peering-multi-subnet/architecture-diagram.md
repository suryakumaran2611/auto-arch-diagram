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
primary… (Private)]
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
