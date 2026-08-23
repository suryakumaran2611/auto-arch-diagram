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

**Architecture** — Minimal AWS web foundation: one VPC containing a single public subnet and a stateful security group governing one EC2 instance. Four resources, four dependency/security edges; no data stores.

**Dataflow** — (1) VPC provisions the public subnet; (2) VPC scopes the security group; (3) subnet hosts the web instance; (4) security group enforces its traffic rules. No ingress edge from an internet gateway, load balancer, or CDN is modeled, so the request path is incomplete.

**Security** — Positive: explicit SG-to-instance binding and clear VPC isolation. Gaps: public-subnet placement without DMZ/private tier; no KMS, Secrets Manager, IAM role, encrypted storage, flow logs, or WAF declared.

**Scalability** — Single instance, single AZ; no ASG or ELB. Adequate for dev/PoC; production needs multi-AZ subnets, horizontal scaling, and defense-in-depth.

**Context hints**
- `[NETWORK]` Single public subnet; no private tier, NAT, or route tables modeled
- `[COMPUTE]` One EC2 instance; no autoscaling group or load balancer present
- `[GENERAL]` No storage, KMS, or secrets resources declared; encryption posture unknown
- `[NETWORK]` Security group provides stateful instance-level access control within VPC

**Contextual labels applied:** `vpc.main` → Isolated Network Boundary, `subnet.public` → Public Subnet Tier, `instance.web` → Web Server Compute, `security_group.web` → Stateful Firewall Rules

**Review notes**
- [grouping] VPC and subnet are rendered both as containers and standalone nodes, duplicating identity and inflating cognitive load
- [edge-routing] Security-group-to-instance dashed edge detours below the subnet boundary instead of routing directly to its target
- [labeling] Container caption 'Subnet public (Public)' duplicates the node label 'Subnet public'; redundant text
- [completeness] No internet gateway, route table, or inbound request data-flow edge; only dependency and security relations shown
- [layout] Security group node sits outside the subnet container although it governs an instance inside it, weakening containment semantics

Feedback iterations: iter0: 7/10, iter1: 6/10, iter2: 6/10

**AI-refined diagram files** (include legend and review hints): architecture-diagram-ai.png, architecture-diagram-ai.jpg, architecture-diagram-ai.svg, architecture-diagram-ai.html, architecture-diagram-ai.drawio
