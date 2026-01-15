<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a best-effort Bicep dependency diagram (dependsOn/parent).

```mermaid
flowchart LR
subgraph Azure[Azure]
  bicep_cdnEndpoint["cdnEndpoint\nMicrosoft.Cdn/profiles/endpoints"]
  bicep_cdnProfile["cdnProfile\nMicrosoft.Cdn/profiles"]
  bicep_rg["rg\nMicrosoft.Resources/resourceGroups"]
  bicep_stg["stg\nMicrosoft.Storage/storageAccounts"]
end
bicep_stg --> bicep_cdnEndpoint
```

Assumptions: Connections represent explicit dependsOn/parent references; implicit property references are not fully resolved.

Rendered diagram: not available (icons require Graphviz + diagrams)
