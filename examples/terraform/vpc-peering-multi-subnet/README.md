# VPC Peering Multi-Subnet (Terraform)

This example models an AWS architecture with:

- Two VPCs (primary and peer)
- Public and private subnet tiers in both VPCs
- A VPC peering connection between the two VPCs
- Route tables and associations for private-subnet communication
- One EC2 workload in each private subnet

Use this example to validate that generated diagrams preserve network hierarchy:

1. Each VPC should render as its own network container.
2. Public/private subnets should render inside their parent VPC.
3. The VPC peering connection should render as a connector resource between VPCs, not as a VPC container.
