<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph all_AWS[AWS]
  subgraph vpc_aws_vpc_main[VPC
main]
    tf_aws_vpc_main["aws_vpc.main"]
    subgraph subnet_aws_subnet_public[Subnet
public (Public)]
      tf_aws_subnet_public["aws_subnet.public"]
      tf_aws_instance_web["aws_instance.web"]
    end
    tf_aws_security_group_web["aws_security_group.web"]
  end
end
tf_aws_security_group_web --> tf_aws_instance_web
tf_aws_subnet_public --> tf_aws_instance_web
tf_aws_vpc_main --> tf_aws_security_group_web
tf_aws_vpc_main --> tf_aws_subnet_public
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact
