<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph all_AWS[AWS]
  subgraph vpc_aws_vpc_main[VPC
main]
    tf_aws_vpc_main["aws_vpc.main"]
    subgraph subnet_aws_subnet_private_1[Subnet
private 1 (Private)]
      tf_aws_subnet_private_1["aws_subnet.private_1"]
      tf_aws_db_instance_main["aws_db_instance.main"]
      tf_aws_elasticache_cluster_main["aws_elasticache_cluster.main"]
    end
    subgraph subnet_aws_subnet_private_2[Subnet
private 2 (Private)]
      tf_aws_subnet_private_2["aws_subnet.private_2"]
    end
    subgraph subnet_aws_subnet_public_1[Subnet
public 1 (Public)]
      tf_aws_subnet_public_1["aws_subnet.public_1"]
      tf_aws_route_table_association_public_1["aws_route_table_association.public_1"]
    end
    subgraph subnet_aws_subnet_public_2[Subnet
public 2 (Public)]
      tf_aws_subnet_public_2["aws_subnet.public_2"]
      tf_aws_route_table_association_public_2["aws_route_table_association.public_2"]
    end
    tf_aws_autoscaling_group_app["aws_autoscaling_group.app"]
    tf_aws_db_subnet_group_main["aws_db_subnet_group.main"]
    tf_aws_elasticache_subnet_group_main["aws_elasticache_subnet_group.main"]
    tf_aws_internet_gateway_main["aws_internet_gateway.main"]
    tf_aws_lb_main["aws_lb.main"]
    tf_aws_lb_target_group_app["aws_lb_target_group.app"]
    tf_aws_route_table_public["aws_route_table.public"]
    tf_aws_security_group_alb["aws_security_group.alb"]
    tf_aws_security_group_app["aws_security_group.app"]
    tf_aws_security_group_database["aws_security_group.database"]
  end
  tf_aws_cloudfront_distribution_main["aws_cloudfront_distribution.main"]
  tf_aws_launch_template_app["aws_launch_template.app"]
  tf_aws_lb_listener_http["aws_lb_listener.http"]
  tf_aws_s3_bucket_static_assets["aws_s3_bucket.static_assets"]
  tf_aws_s3_bucket_public_access_block_static_assets["aws_s3_bucket_public_access_block.static_assets"]
  tf_aws_s3_bucket_versioning_static_assets["aws_s3_bucket_versioning.static_assets"]
end
tf_aws_db_subnet_group_main --> tf_aws_db_instance_main
tf_aws_elasticache_subnet_group_main --> tf_aws_elasticache_cluster_main
tf_aws_internet_gateway_main --> tf_aws_route_table_public
tf_aws_launch_template_app --> tf_aws_autoscaling_group_app
tf_aws_lb_main --> tf_aws_cloudfront_distribution_main
tf_aws_lb_main --> tf_aws_lb_listener_http
tf_aws_lb_target_group_app --> tf_aws_autoscaling_group_app
tf_aws_lb_target_group_app --> tf_aws_lb_listener_http
tf_aws_route_table_public --> tf_aws_route_table_association_public_1
tf_aws_route_table_public --> tf_aws_route_table_association_public_2
tf_aws_s3_bucket_static_assets --> tf_aws_s3_bucket_public_access_block_static_assets
tf_aws_s3_bucket_static_assets --> tf_aws_s3_bucket_versioning_static_assets
tf_aws_security_group_alb --> tf_aws_lb_main
tf_aws_security_group_alb --> tf_aws_security_group_app
tf_aws_security_group_app --> tf_aws_elasticache_cluster_main
tf_aws_security_group_app --> tf_aws_security_group_database
tf_aws_security_group_database --> tf_aws_db_instance_main
tf_aws_subnet_private_1 --> tf_aws_autoscaling_group_app
tf_aws_subnet_private_1 --> tf_aws_db_subnet_group_main
tf_aws_subnet_private_1 --> tf_aws_elasticache_subnet_group_main
tf_aws_subnet_private_2 --> tf_aws_autoscaling_group_app
tf_aws_subnet_private_2 --> tf_aws_db_subnet_group_main
tf_aws_subnet_private_2 --> tf_aws_elasticache_subnet_group_main
tf_aws_subnet_public_1 --> tf_aws_lb_main
tf_aws_subnet_public_1 --> tf_aws_route_table_association_public_1
tf_aws_subnet_public_2 --> tf_aws_lb_main
tf_aws_subnet_public_2 --> tf_aws_route_table_association_public_2
tf_aws_vpc_main --> tf_aws_internet_gateway_main
tf_aws_vpc_main --> tf_aws_lb_target_group_app
tf_aws_vpc_main --> tf_aws_route_table_public
tf_aws_vpc_main --> tf_aws_security_group_alb
tf_aws_vpc_main --> tf_aws_security_group_app
tf_aws_vpc_main --> tf_aws_security_group_database
tf_aws_vpc_main --> tf_aws_subnet_private_1
tf_aws_vpc_main --> tf_aws_subnet_private_2
tf_aws_vpc_main --> tf_aws_subnet_public_1
tf_aws_vpc_main --> tf_aws_subnet_public_2
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact

## AI Architecture Insights

*Reviewed by OpenRouter free vision model `stealth/ox-alpha` (quality score: 5/10).*

Internet users reach **cloudfront_distribution.main**, which origins to **lb.main**'s HTTP listener in `public_1`/`public_2`. **lb_target_group.app** routes requests to EC2 instances defined by **launch_template.app** and scaled by **autoscaling_group.app** across `private_1`/`private_2`. Instances read/write **db_instance.main** via **db_subnet_group.main** and query **elasticache_cluster.main** for caching. Ingress is tiered through security groups alb→app→database. **static_assets** keeps versioned build artifacts with public access blocked; notably, no CloudFront–S3 origin edge exists, so asset delivery stays undefined in this graph.

**Context hints**
- `[S3]` static_assets stores versioned site assets; public_access_block forbids all public access.
- `[NETWORK]` cloudfront_distribution.main fronts lb.main as CDN edge for app traffic.
- `[COMPUTE]` launch_template.app defines instances; autoscaling_group.app scales them across private_1, private_2.
- `[NETWORK]` lb_listener.http accepts HTTP; lb_target_group.app forwards to autoscaling_group.app.
- `[IAM]` security_group.alb permits lb.main ingress; chained rules gate app then database.
- `[DATA]` app tier consumes db_instance.main and elasticache_cluster.main inside private subnets.

**Contextual labels applied:** `static_assets` → Static Assets (Versioned), `cloudfront_distribution` → Edge CDN Entry, `lb` → Public Load Balancer, `lb_listener_http` → HTTP Listener, `lb_target_group_app` → App Target Pool, `autoscaling_group_app` → App Instance Fleet (+4 more)

**Review notes**
- [labeling] Several labels truncate mid-word: 'S3 Bucket Public...', 'Route Table...', 'CloudFront...', 'Elasticache Subnet...' obscure resource identity.
- [edge-routing] Dashed red security-group edges span the entire VPC canvas, crossing subnet frames and solid data-path edges repeatedly.
- [layout] autoscaling_group.app renders outside the VPC boundary despite deploying into private_1/private_2; long edges stretch from lower-left to far right.
- [grouping] 'Other' lumps edge-tier CloudFront with compute Launch Template; the Storage group floats detached from its consumers.
- [completeness] No depicted relationship between cloudfront_distribution.main and s3_bucket.static_assets leaves the asset-serving flow ambiguous.

Feedback iterations: iter0: 4/10, iter1: 5/10, iter2: 4/10, iter3: 4/10

**AI-refined diagram files** (include legend and review hints): architecture-diagram-ai.png, architecture-diagram-ai.jpg, architecture-diagram-ai.svg
