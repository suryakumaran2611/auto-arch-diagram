<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a Pulumi YAML diagram from resources and dependsOn/reference expressions.

```mermaid
flowchart LR
subgraph AZURE-NATIVE[AZURE-NATIVE]
  pulumi_cdnProfile["cdnProfile\nazure-native:cdn:Profile"]
  pulumi_rg["rg\nazure-native:resources:ResourceGroup"]
  pulumi_stg["stg\nazure-native:storage:StorageAccount"]
end
pulumi_rg --> pulumi_cdnProfile
pulumi_rg --> pulumi_stg
```

Assumptions: Connections represent options.dependsOn and ${resource.property} references in YAML.

Rendered diagram: not available (icons require Graphviz + diagrams)
