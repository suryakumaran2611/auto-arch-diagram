<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph GCP[GCP]
  tf_google_compute_backend_bucket_cdn["google_compute_backend_bucket.cdn"]
  tf_google_compute_global_forwarding_rule_lb["google_compute_global_forwarding_rule.lb"]
  tf_google_compute_managed_ssl_certificate_cert["google_compute_managed_ssl_certificate.cert"]
  tf_google_compute_security_policy_waf["google_compute_security_policy.waf"]
  tf_google_compute_target_https_proxy_lb["google_compute_target_https_proxy.lb"]
  tf_google_compute_url_map_lb["google_compute_url_map.lb"]
  tf_google_storage_bucket_logs["google_storage_bucket.logs"]
  tf_google_storage_bucket_site["google_storage_bucket.site"]
end
tf_google_compute_backend_bucket_cdn --> tf_google_compute_url_map_lb
tf_google_compute_managed_ssl_certificate_cert --> tf_google_compute_target_https_proxy_lb
tf_google_compute_security_policy_waf --> tf_google_compute_backend_bucket_cdn
tf_google_compute_target_https_proxy_lb --> tf_google_compute_global_forwarding_rule_lb
tf_google_compute_url_map_lb --> tf_google_compute_target_https_proxy_lb
tf_google_storage_bucket_site --> tf_google_compute_backend_bucket_cdn
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact
