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

## AI Architecture Insights

*Reviewed by OpenRouter free vision model `stealth/ox-alpha` (quality score: 7/10).*

**Single-VPC AWS web foundation.** `aws_vpc.main` defines the isolated network; `aws_subnet.public` carves a public subnet intended for internet-facing traffic. `aws_instance.web` launches as the sole EC2 workload host inside that subnet. `aws_security_group.web` attaches to the instance as its stateful firewall, governing inbound rules. **Flow:** client traffic enters via the public subnet, passes security-group inspection, reaches the instance. Missing: no internet gateway, route table, load balancer, data stores, or secrets — persistence and HA are out of scope. Single-AZ layout implies no redundancy.

**Context hints**
- `[NETWORK]` aws_vpc.main provides isolated address space enclosing all three child resources.
- `[NETWORK]` aws_subnet.public assigns routable addresses to aws_instance.web within aws_vpc.main.
- `[COMPUTE]` aws_instance.web is sole compute host, exposed through public subnet path.
- `[NETWORK]` aws_security_group.web stateful firewall filtering ingress traffic destined to aws_instance.web.
- `[GENERAL]` No internet gateway or route table inventoried; public reachability unverified.

**Contextual labels applied:** `vpc_main` → VPC Isolation Boundary, `subnet_public` → Public Web Tier Subnet, `security_group_web` → Web Ingress Firewall, `instance_web` → Web Server Host

**Review notes**
- [grouping] Triple nesting (Network > AWS Cloud > VPC main) consumes most canvas for only four resources.
- [labeling] 'Subnet public' rendered twice: group header 'Subnet public (Public)' plus duplicate node caption.
- [edge-routing] security_group_web to instance_web edge detours above the subnet box instead of short direct hop.
- [completeness] Subnet labeled Public but no route table or internet gateway node shown.

Feedback iterations: iter0: 7/10, iter1: 6/10, iter2: 6/10

**AI-refined diagram files** (include legend and review hints): architecture-diagram-ai.png, architecture-diagram-ai.jpg, architecture-diagram-ai.svg
