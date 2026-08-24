<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph all_AWS["AWS"]
  subgraph vpc_aws_vpc_app_vpc["VPC app vpc"]
    tf_aws_vpc_app_vpc["aws_vpc.app_vpc"]
    subgraph subnet_aws_subnet_private_1["Subnet private 1 (Private)"]
      tf_aws_subnet_private_1["aws_subnet.private_1"]
    end
    subgraph subnet_aws_subnet_public_1["Subnet public 1 (Public)"]
      tf_aws_subnet_public_1["aws_subnet.public_1"]
    end
  end
  tf_aws_apigatewayv2_api_http_api["aws_apigatewayv2_api.http_api"]
  tf_aws_apprunner_service_api_service["aws_apprunner_service.api_service"]
  tf_aws_elasticache_cluster_redis_cache["aws_elasticache_cluster.redis_cache"]
  tf_aws_kms_key_app_encryption_key["aws_kms_key.app_encryption_key"]
  tf_aws_rds_cluster_aurora_postgres["aws_rds_cluster.aurora_postgres"]
  tf_aws_s3_bucket_artifacts_bucket["aws_s3_bucket.artifacts_bucket"]
end
tf_aws_vpc_app_vpc --> tf_aws_subnet_private_1
tf_aws_vpc_app_vpc --> tf_aws_subnet_public_1
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact
