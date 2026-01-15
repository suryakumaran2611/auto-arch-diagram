<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a Pulumi YAML diagram from resources and dependsOn/reference expressions.

```mermaid
flowchart LR
subgraph IBM[IBM]
  pulumi_cos["cos\nibm:resource/instance:Instance"]
  pulumi_siteBucket["siteBucket\nibm:cos/bucket:Bucket"]
end
pulumi_cos --> pulumi_siteBucket
```

Assumptions: Connections represent options.dependsOn and ${resource.property} references in YAML.

Rendered diagram: not available (icons require Graphviz + diagrams)
