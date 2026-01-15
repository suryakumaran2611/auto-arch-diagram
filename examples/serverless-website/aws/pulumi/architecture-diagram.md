<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a Pulumi YAML diagram from resources and dependsOn/reference expressions.

```mermaid
flowchart LR
subgraph AWS[AWS]
  pulumi_cdn["cdn\naws:cloudfront/distribution:Distribution"]
  pulumi_siteBucket["siteBucket\naws:s3/bucket:Bucket"]
  pulumi_waf["waf\naws:wafv2/webAcl:WebAcl"]
end
pulumi_siteBucket --> pulumi_cdn
pulumi_waf --> pulumi_cdn
```

Assumptions: Connections represent options.dependsOn and ${resource.property} references in YAML.

Rendered diagram: not available (icons require Graphviz + diagrams)
