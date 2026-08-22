<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented Terraform diagram from changed resources.

```mermaid
flowchart LR
subgraph all_AWS[AWS]
  subgraph vpc_aws_vpc_app_vpc[VPC
app vpc]
    tf_aws_vpc_app_vpc["aws_vpc.app_vpc"]
    subgraph subnet_aws_subnet_private_app_subnet_az1[Subnet
private app subnet… (Private)]
      tf_aws_subnet_private_app_subnet_az1["aws_subnet.private_app_subnet_az1"]
      tf_aws_efs_mount_target_mount_az1["aws_efs_mount_target.mount_az1"]
      tf_aws_route_table_association_private_rt_assoc_az1["aws_route_table_association.private_rt_assoc_az1"]
    end
    subgraph subnet_aws_subnet_private_app_subnet_az2[Subnet
private app subnet… (Private)]
      tf_aws_subnet_private_app_subnet_az2["aws_subnet.private_app_subnet_az2"]
      tf_aws_efs_mount_target_mount_az2["aws_efs_mount_target.mount_az2"]
      tf_aws_route_table_association_private_rt_assoc_az2["aws_route_table_association.private_rt_assoc_az2"]
    end
    subgraph subnet_aws_subnet_private_data_subnet_az1[Subnet
private data subnet… (Private)]
      tf_aws_subnet_private_data_subnet_az1["aws_subnet.private_data_subnet_az1"]
      tf_aws_db_instance_postgres_db["aws_db_instance.postgres_db"]
      tf_aws_elasticache_replication_group_redis_replication_group["aws_elasticache_replication_group.redis_replication_group"]
    end
    subgraph subnet_aws_subnet_private_data_subnet_az2[Subnet
private data subnet… (Private)]
      tf_aws_subnet_private_data_subnet_az2["aws_subnet.private_data_subnet_az2"]
    end
    subgraph subnet_aws_subnet_public_subnet_az1[Subnet
public subnet az1 (Public)]
      tf_aws_subnet_public_subnet_az1["aws_subnet.public_subnet_az1"]
      tf_aws_nat_gateway_app_nat_gw_az1["aws_nat_gateway.app_nat_gw_az1"]
      tf_aws_route_table_association_public_rt_assoc_az1["aws_route_table_association.public_rt_assoc_az1"]
    end
    subgraph subnet_aws_subnet_public_subnet_az2[Subnet
public subnet az2 (Public)]
      tf_aws_subnet_public_subnet_az2["aws_subnet.public_subnet_az2"]
      tf_aws_route_table_association_public_rt_assoc_az2["aws_route_table_association.public_rt_assoc_az2"]
    end
    tf_aws_db_subnet_group_db_subnet_group["aws_db_subnet_group.db_subnet_group"]
    tf_aws_elasticache_subnet_group_cache_subnet_group["aws_elasticache_subnet_group.cache_subnet_group"]
    tf_aws_internet_gateway_app_igw["aws_internet_gateway.app_igw"]
    tf_aws_lb_app_alb["aws_lb.app_alb"]
    tf_aws_lb_target_group_app_target_group["aws_lb_target_group.app_target_group"]
    tf_aws_route_table_private_route_table["aws_route_table.private_route_table"]
    tf_aws_route_table_public_route_table["aws_route_table.public_route_table"]
    tf_aws_security_group_alb_security_group["aws_security_group.alb_security_group"]
    tf_aws_security_group_db_security_group["aws_security_group.db_security_group"]
    tf_aws_security_group_ecs_tasks_security_group["aws_security_group.ecs_tasks_security_group"]
    tf_aws_security_group_efs_security_group["aws_security_group.efs_security_group"]
    tf_aws_security_group_redis_security_group["aws_security_group.redis_security_group"]
  end
  tf_aws_application_autoscaling_target_service_scaling_target["aws_application_autoscaling_target.service_scaling_target"]
  tf_aws_cloudwatch_log_group_app_log_group["aws_cloudwatch_log_group.app_log_group"]
  tf_aws_cloudwatch_metric_alarm_alb_5xx_alarm["aws_cloudwatch_metric_alarm.alb_5xx_alarm"]
  tf_aws_cloudwatch_metric_alarm_rds_cpu_alarm["aws_cloudwatch_metric_alarm.rds_cpu_alarm"]
  tf_aws_ecr_repository_app_repository["aws_ecr_repository.app_repository"]
  subgraph cluster_aws_ecs_cluster_app_cluster[Ecs Cluster
app cluster]
    tf_aws_ecs_cluster_app_cluster["aws_ecs_cluster.app_cluster"]
    tf_aws_ecs_service_app_service["aws_ecs_service.app_service"]
  end
  tf_aws_ecs_task_definition_app_task_definition["aws_ecs_task_definition.app_task_definition"]
  tf_aws_efs_access_point_static_assets_ap["aws_efs_access_point.static_assets_ap"]
  tf_aws_efs_file_system_app_file_system["aws_efs_file_system.app_file_system"]
  tf_aws_eip_nat_gw_elastic_ip_az1["aws_eip.nat_gw_elastic_ip_az1"]
  tf_aws_iam_role_ecs_task_execution_role["aws_iam_role.ecs_task_execution_role"]
  tf_aws_iam_role_ecs_task_role["aws_iam_role.ecs_task_role"]
  tf_aws_iam_role_policy_attachment_ecs_task_execution_policy["aws_iam_role_policy_attachment.ecs_task_execution_policy"]
  tf_aws_kms_alias_data_encryption_key_alias["aws_kms_alias.data_encryption_key_alias"]
  tf_aws_kms_key_data_encryption_key["aws_kms_key.data_encryption_key"]
  tf_aws_lb_listener_http_redirect_listener["aws_lb_listener.http_redirect_listener"]
  tf_aws_lb_listener_https_listener["aws_lb_listener.https_listener"]
  tf_aws_s3_bucket_assets_bucket["aws_s3_bucket.assets_bucket"]
  tf_aws_s3_bucket_lifecycle_configuration_assets_lifecycle["aws_s3_bucket_lifecycle_configuration.assets_lifecycle"]
  tf_aws_s3_bucket_public_access_block_assets_pab["aws_s3_bucket_public_access_block.assets_pab"]
  tf_aws_s3_bucket_server_side_encryption_configuration_assets_encryption["aws_s3_bucket_server_side_encryption_configuration.assets_encryption"]
  tf_aws_s3_bucket_versioning_assets_versioning["aws_s3_bucket_versioning.assets_versioning"]
  tf_aws_secretsmanager_secret_db_credentials_secret["aws_secretsmanager_secret.db_credentials_secret"]
  tf_aws_secretsmanager_secret_version_db_credentials_version["aws_secretsmanager_secret_version.db_credentials_version"]
  tf_aws_sns_topic_ops_alerts_topic["aws_sns_topic.ops_alerts_topic"]
  tf_aws_sns_topic_subscription_ops_email_subscription["aws_sns_topic_subscription.ops_email_subscription"]
  tf_aws_ssm_parameter_app_feature_flags["aws_ssm_parameter.app_feature_flags"]
  tf_aws_wafv2_web_acl_alb_web_acl["aws_wafv2_web_acl.alb_web_acl"]
  tf_aws_wafv2_web_acl_association_alb_waf_assoc["aws_wafv2_web_acl_association.alb_waf_assoc"]
end
subgraph all_RANDOM[RANDOM]
  tf_random_password_db_master_password["random_password.db_master_password"]
end
tf_aws_cloudwatch_log_group_app_log_group --> tf_aws_ecs_task_definition_app_task_definition
tf_aws_db_instance_postgres_db --> tf_aws_cloudwatch_metric_alarm_rds_cpu_alarm
tf_aws_db_instance_postgres_db --> tf_aws_secretsmanager_secret_version_db_credentials_version
tf_aws_db_subnet_group_db_subnet_group --> tf_aws_db_instance_postgres_db
tf_aws_ecs_cluster_app_cluster --> tf_aws_application_autoscaling_target_service_scaling_target
tf_aws_ecs_cluster_app_cluster --> tf_aws_ecs_service_app_service
tf_aws_ecs_service_app_service --> tf_aws_application_autoscaling_target_service_scaling_target
tf_aws_ecs_task_definition_app_task_definition --> tf_aws_ecs_service_app_service
tf_aws_eip_nat_gw_elastic_ip_az1 --> tf_aws_nat_gateway_app_nat_gw_az1
tf_aws_elasticache_subnet_group_cache_subnet_group --> tf_aws_elasticache_replication_group_redis_replication_group
tf_aws_iam_role_ecs_task_execution_role --> tf_aws_ecs_task_definition_app_task_definition
tf_aws_iam_role_ecs_task_execution_role --> tf_aws_iam_role_policy_attachment_ecs_task_execution_policy
tf_aws_iam_role_ecs_task_role --> tf_aws_ecs_task_definition_app_task_definition
tf_aws_internet_gateway_app_igw --> tf_aws_nat_gateway_app_nat_gw_az1
tf_aws_internet_gateway_app_igw --> tf_aws_route_table_public_route_table
tf_aws_kms_key_data_encryption_key --> tf_aws_cloudwatch_log_group_app_log_group
tf_aws_kms_key_data_encryption_key --> tf_aws_db_instance_postgres_db
tf_aws_kms_key_data_encryption_key --> tf_aws_efs_file_system_app_file_system
tf_aws_kms_key_data_encryption_key --> tf_aws_elasticache_replication_group_redis_replication_group
tf_aws_kms_key_data_encryption_key --> tf_aws_kms_alias_data_encryption_key_alias
tf_aws_kms_key_data_encryption_key --> tf_aws_s3_bucket_server_side_encryption_configuration_assets_encryption
tf_aws_kms_key_data_encryption_key --> tf_aws_secretsmanager_secret_db_credentials_secret
tf_aws_kms_key_data_encryption_key --> tf_aws_sns_topic_ops_alerts_topic
tf_aws_lb_app_alb --> tf_aws_cloudwatch_metric_alarm_alb_5xx_alarm
tf_aws_lb_app_alb --> tf_aws_lb_listener_http_redirect_listener
tf_aws_lb_app_alb --> tf_aws_lb_listener_https_listener
tf_aws_lb_app_alb --> tf_aws_wafv2_web_acl_association_alb_waf_assoc
tf_aws_lb_target_group_app_target_group --> tf_aws_ecs_service_app_service
tf_aws_lb_target_group_app_target_group --> tf_aws_lb_listener_https_listener
tf_aws_nat_gateway_app_nat_gw_az1 --> tf_aws_route_table_private_route_table
tf_aws_route_table_private_route_table --> tf_aws_route_table_association_private_rt_assoc_az1
tf_aws_route_table_private_route_table --> tf_aws_route_table_association_private_rt_assoc_az2
tf_aws_route_table_public_route_table --> tf_aws_route_table_association_public_rt_assoc_az1
tf_aws_route_table_public_route_table --> tf_aws_route_table_association_public_rt_assoc_az2
tf_aws_s3_bucket_assets_bucket --> tf_aws_s3_bucket_lifecycle_configuration_assets_lifecycle
tf_aws_s3_bucket_assets_bucket --> tf_aws_s3_bucket_public_access_block_assets_pab
tf_aws_s3_bucket_assets_bucket --> tf_aws_s3_bucket_server_side_encryption_configuration_assets_encryption
tf_aws_s3_bucket_assets_bucket --> tf_aws_s3_bucket_versioning_assets_versioning
tf_aws_secretsmanager_secret_db_credentials_secret --> tf_aws_ecs_task_definition_app_task_definition
tf_aws_secretsmanager_secret_db_credentials_secret --> tf_aws_secretsmanager_secret_version_db_credentials_version
tf_aws_security_group_alb_security_group --> tf_aws_lb_app_alb
tf_aws_security_group_alb_security_group --> tf_aws_security_group_ecs_tasks_security_group
tf_aws_security_group_db_security_group --> tf_aws_db_instance_postgres_db
tf_aws_security_group_ecs_tasks_security_group --> tf_aws_ecs_service_app_service
tf_aws_security_group_ecs_tasks_security_group --> tf_aws_security_group_alb_security_group
tf_aws_security_group_ecs_tasks_security_group --> tf_aws_security_group_db_security_group
tf_aws_security_group_ecs_tasks_security_group --> tf_aws_security_group_efs_security_group
tf_aws_security_group_ecs_tasks_security_group --> tf_aws_security_group_redis_security_group
tf_aws_security_group_efs_security_group --> tf_aws_efs_mount_target_mount_az1
tf_aws_security_group_efs_security_group --> tf_aws_efs_mount_target_mount_az2
tf_aws_security_group_redis_security_group --> tf_aws_elasticache_replication_group_redis_replication_group
tf_aws_sns_topic_ops_alerts_topic --> tf_aws_cloudwatch_metric_alarm_alb_5xx_alarm
tf_aws_sns_topic_ops_alerts_topic --> tf_aws_cloudwatch_metric_alarm_rds_cpu_alarm
tf_aws_sns_topic_ops_alerts_topic --> tf_aws_sns_topic_subscription_ops_email_subscription
tf_aws_subnet_private_app_subnet_az1 --> tf_aws_ecs_service_app_service
tf_aws_subnet_private_app_subnet_az1 --> tf_aws_efs_mount_target_mount_az1
tf_aws_subnet_private_app_subnet_az1 --> tf_aws_route_table_association_private_rt_assoc_az1
tf_aws_subnet_private_app_subnet_az2 --> tf_aws_ecs_service_app_service
tf_aws_subnet_private_app_subnet_az2 --> tf_aws_efs_mount_target_mount_az2
tf_aws_subnet_private_app_subnet_az2 --> tf_aws_route_table_association_private_rt_assoc_az2
tf_aws_subnet_private_data_subnet_az1 --> tf_aws_db_subnet_group_db_subnet_group
tf_aws_subnet_private_data_subnet_az1 --> tf_aws_elasticache_subnet_group_cache_subnet_group
tf_aws_subnet_private_data_subnet_az2 --> tf_aws_db_subnet_group_db_subnet_group
tf_aws_subnet_private_data_subnet_az2 --> tf_aws_elasticache_subnet_group_cache_subnet_group
tf_aws_subnet_public_subnet_az1 --> tf_aws_lb_app_alb
tf_aws_subnet_public_subnet_az1 --> tf_aws_nat_gateway_app_nat_gw_az1
tf_aws_subnet_public_subnet_az1 --> tf_aws_route_table_association_public_rt_assoc_az1
tf_aws_subnet_public_subnet_az2 --> tf_aws_lb_app_alb
tf_aws_subnet_public_subnet_az2 --> tf_aws_route_table_association_public_rt_assoc_az2
tf_aws_vpc_app_vpc --> tf_aws_internet_gateway_app_igw
tf_aws_vpc_app_vpc --> tf_aws_lb_target_group_app_target_group
tf_aws_vpc_app_vpc --> tf_aws_route_table_private_route_table
tf_aws_vpc_app_vpc --> tf_aws_route_table_public_route_table
tf_aws_vpc_app_vpc --> tf_aws_security_group_alb_security_group
tf_aws_vpc_app_vpc --> tf_aws_security_group_db_security_group
tf_aws_vpc_app_vpc --> tf_aws_security_group_ecs_tasks_security_group
tf_aws_vpc_app_vpc --> tf_aws_security_group_efs_security_group
tf_aws_vpc_app_vpc --> tf_aws_security_group_redis_security_group
tf_aws_vpc_app_vpc --> tf_aws_subnet_private_app_subnet_az1
tf_aws_vpc_app_vpc --> tf_aws_subnet_private_app_subnet_az2
tf_aws_vpc_app_vpc --> tf_aws_subnet_private_data_subnet_az1
tf_aws_vpc_app_vpc --> tf_aws_subnet_private_data_subnet_az2
tf_aws_vpc_app_vpc --> tf_aws_subnet_public_subnet_az1
tf_aws_vpc_app_vpc --> tf_aws_subnet_public_subnet_az2
tf_aws_wafv2_web_acl_alb_web_acl --> tf_aws_lb_listener_https_listener
tf_aws_wafv2_web_acl_alb_web_acl --> tf_aws_wafv2_web_acl_association_alb_waf_assoc
```

Assumptions: Connections represent inferred references (including depends_on and attribute references).

Rendered diagram: available as workflow artifact

## AI Architecture Insights

*Reviewed by OpenRouter free vision model `stealth/ox-alpha` (quality score: 4/10).*

**End-to-end:** Public traffic reaches `app_alb` in public subnets, passes `alb_web_acl` inspection, lands on `https_listener` (`http_redirect_listener` enforces TLS), then routes via `app_target_group` to `app_service` tasks in private app subnets across two AZs.

Tasks query `postgres_db`, cache in `redis_replication_group`, mount `app_file_system` via per-AZ EFS targets, and serve static files from `assets_bucket` (versioned, lifecycle-managed, KMS-encrypted, public access blocked).

`data_encryption_key` uniformly encrypts storage services; `db_credentials_secret` injects DB credentials into `app_task_definition`. Alarms on ALB 5xx and RDS CPU fan out through `ops_alerts_topic` to operator email.

**Context hints**
- `[KMS]` data_encryption_key encrypts RDS, EFS, Redis, SNS, secrets, logs, and S3.
- `[SECRETS]` db_credentials_secret holds postgres_db master password; app_task_definition consumes it.
- `[S3]` assets_bucket stores static assets; versioned, lifecycle rules, KMS-encrypted, public access blocked.
- `[NETWORK]` app_alb terminates TLS on https_listener; http_redirect_listener forces HTTPS inbound.
- `[COMPUTE]` app_service tasks in private subnets use postgres_db, redis_replication_group, app_file_system mounts.
- `[GENERAL]` alb_5xx_alarm and rds_cpu_alarm publish to ops_alerts_topic; ops_email_subscription emails operators.

**Contextual labels applied:** `assets_bucket` → Static Assets (Versioned), `postgres_db` → Primary PostgreSQL Database, `redis_replication_group` → Redis Cache Replication Group, `app_alb` → Public HTTPS Entry Point, `app_service` → Containerized App (Autoscaled), `data_encryption_key` → Central Encryption Key (+6 more)

**Review notes**
- [layout] Extreme vertical sprawl; Security cluster sits far above its Network/Storage consumers, forcing full-height dashed edges.
- [labeling] Many node labels truncated mid-word ('ecs task execution...', 'db credentials...', 'Ssm Parameter').
- [grouping] 'Other' is a catch-all mixing logging, secrets, messaging, config, and alarms, obscuring functional tiers.
- [edge-routing] Dense crossings among NAT gateway, route tables, and security groups; KMS fan-out overlaps every other flow.
- [completeness] Orphan nodes with zero edges: app_repository, app_feature_flags, db_master_password hide real dependencies.

Feedback iterations: iter0: 3/10, iter1: 3/10, iter2: 4/10

**AI-refined diagram files** (include legend and review hints): architecture-diagram-ai.png, architecture-diagram-ai.jpg, architecture-diagram-ai.svg
