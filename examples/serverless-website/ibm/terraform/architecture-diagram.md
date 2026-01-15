<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph IBM[IBM]
  tf_ibm_cos_bucket_site["ibm_cos_bucket.site"]
  tf_ibm_resource_instance_cos["ibm_resource_instance.cos"]
end
tf_ibm_resource_instance_cos --> tf_ibm_cos_bucket_site
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact
