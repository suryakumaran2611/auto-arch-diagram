<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph GOOGLE[GOOGLE]
  tf_google_compute_backend_bucket_cdn["google_compute_backend_bucket.cdn"]
  tf_google_compute_security_policy_waf["google_compute_security_policy.waf"]
  tf_google_storage_bucket_site["google_storage_bucket.site"]
end
tf_google_compute_security_policy_waf --> tf_google_compute_backend_bucket_cdn
tf_google_storage_bucket_site --> tf_google_compute_backend_bucket_cdn
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: not available (icons require Graphviz + diagrams)
