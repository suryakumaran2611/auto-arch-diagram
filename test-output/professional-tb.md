<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart TB
subgraph AWS[AWS]
  tf_aws_instance_web["aws_instance.web"]
  tf_aws_security_group_web["aws_security_group.web"]
  tf_aws_subnet_public["aws_subnet.public"]
  tf_aws_vpc_main["aws_vpc.main"]
end
tf_aws_security_group_web --> tf_aws_instance_web
tf_aws_subnet_public --> tf_aws_instance_web
tf_aws_vpc_main --> tf_aws_security_group_web
tf_aws_vpc_main --> tf_aws_subnet_public
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact
