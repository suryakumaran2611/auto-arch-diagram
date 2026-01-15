<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a Pulumi YAML diagram from resources and dependsOn/reference expressions.

```mermaid
flowchart LR
subgraph GCP[GCP]
  pulumi_cdn["cdn\ngcp:compute/backendBucket:BackendBucket"]
  pulumi_siteBucket["siteBucket\ngcp:storage/bucket:Bucket"]
end
pulumi_siteBucket --> pulumi_cdn
```

Assumptions: Connections represent options.dependsOn and ${resource.property} references in YAML.

Rendered diagram: not available (icons require Graphviz + diagrams)
