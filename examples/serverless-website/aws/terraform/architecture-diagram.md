<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
  subgraph all_AWS[AWS]
    tf_aws_cloudfront_distribution_cdn["aws_cloudfront_distribution.cdn"]
    tf_aws_cloudfront_function_rewrite_uri["aws_cloudfront_function.rewrite_uri"]
    tf_aws_cloudfront_origin_access_control_oac["aws_cloudfront_origin_access_control.oac"]
    tf_aws_s3_bucket_logs["aws_s3_bucket.logs"]
    tf_aws_s3_bucket_site["aws_s3_bucket.site"]
    tf_aws_s3_bucket_logging_site["aws_s3_bucket_logging.site"]
    tf_aws_s3_bucket_public_access_block_site["aws_s3_bucket_public_access_block.site"]
    tf_aws_s3_bucket_server_side_encryption_configuration_logs["aws_s3_bucket_server_side_encryption_configuration.logs"]
    tf_aws_s3_bucket_server_side_encryption_configuration_site["aws_s3_bucket_server_side_encryption_configuration.site"]
    tf_aws_s3_bucket_versioning_site["aws_s3_bucket_versioning.site"]
    tf_aws_wafv2_web_acl_cdn["aws_wafv2_web_acl.cdn"]
  end
tf_aws_cloudfront_function_rewrite_uri --> tf_aws_cloudfront_distribution_cdn
tf_aws_cloudfront_origin_access_control_oac --> tf_aws_cloudfront_distribution_cdn
tf_aws_s3_bucket_logs --> tf_aws_cloudfront_distribution_cdn
tf_aws_s3_bucket_logs --> tf_aws_s3_bucket_logging_site
tf_aws_s3_bucket_logs --> tf_aws_s3_bucket_server_side_encryption_configuration_logs
tf_aws_s3_bucket_public_access_block_site --> tf_aws_cloudfront_distribution_cdn
tf_aws_s3_bucket_site --> tf_aws_cloudfront_distribution_cdn
tf_aws_s3_bucket_site --> tf_aws_s3_bucket_logging_site
tf_aws_s3_bucket_site --> tf_aws_s3_bucket_public_access_block_site
tf_aws_s3_bucket_site --> tf_aws_s3_bucket_server_side_encryption_configuration_site
tf_aws_s3_bucket_site --> tf_aws_s3_bucket_versioning_site
tf_aws_wafv2_web_acl_cdn --> tf_aws_cloudfront_distribution_cdn
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact
