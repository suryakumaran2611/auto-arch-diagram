#!/usr/bin/env python3
"""
Intelligent Service Mappings Updater
=====================================
Introspects the installed `diagrams` library to build an accurate
comprehensive_service_mappings.json that maps Terraform resource types
to real diagrams library classes.

Usage:
    python tools/update_service_mappings.py               # update in-place
    python tools/update_service_mappings.py --dry-run     # show changes only
    python tools/update_service_mappings.py --force       # overwrite all entries

The script:
  1. Walks all modules in diagrams.{aws,azure,gcp,oci,ibm,k8s,onprem}
  2. Builds a verified index of {provider -> module -> [ClassName, ...]}
  3. Applies curated Terraform-resource-type → (module, ClassName) rules
  4. Falls back to fuzzy heuristics for types not in the curated list
  5. Validates every entry actually imports correctly
  6. Merges with the existing JSON (preserving custom entries, removing
     entries whose class no longer exists, detecting new library additions)
  7. Reports a full diff/summary so you always know what changed
"""

from __future__ import annotations

import argparse
import importlib
import json
import pkgutil
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROVIDERS = ["aws", "azure", "gcp", "oci", "ibm"]
OUTPUT_FILE = Path(__file__).parent / "comprehensive_service_mappings.json"

# ---------------------------------------------------------------------------
# Step 1: Introspect the diagrams library
# ---------------------------------------------------------------------------

def _introspect_provider(provider: str) -> dict[str, dict[str, list[str]]]:
    """Return {module_short_name: [ClassName, ...]} for a provider."""
    result: dict[str, list[str]] = {}
    try:
        pmod = importlib.import_module(f"diagrams.{provider}")
    except ImportError:
        print(f"  [SKIP] diagrams.{provider} not installed")
        return result

    path = getattr(pmod, "__path__", [])
    prefix = f"diagrams.{provider}."

    for _, modname, _ in pkgutil.walk_packages(path=path, prefix=prefix):
        short = modname[len(prefix):]          # e.g. "compute", "network"
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        classes = [
            name for name in dir(mod)
            if not name.startswith("_")
            and isinstance(getattr(mod, name, None), type)
        ]
        if classes:
            result[short] = classes
    return result


def introspect_all() -> dict[str, dict[str, list[str]]]:
    """Introspect all configured providers."""
    index: dict[str, dict[str, list[str]]] = {}
    for prov in PROVIDERS:
        print(f"  Introspecting diagrams.{prov} …")
        index[prov] = _introspect_provider(prov)
        total = sum(len(v) for v in index[prov].values())
        print(f"    → {len(index[prov])} modules, {total} classes")
    return index


# ---------------------------------------------------------------------------
# Step 2: Verify an entry exists in the library
# ---------------------------------------------------------------------------

def _class_exists(provider: str, module: str, cls: str) -> bool:
    """Return True if diagrams.<provider>.<module>.<cls> is importable."""
    try:
        mod = importlib.import_module(f"diagrams.{provider}.{module}")
        return hasattr(mod, cls)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Step 3: Curated Terraform → diagrams mapping rules
# ---------------------------------------------------------------------------
# Format:  "terraform_key": ("module", "ClassName")
# terraform_key: the resource type stripped of the provider prefix and joined
#                with underscores, e.g. for aws_lambda_function → "lambda_function"

CURATED_RULES: dict[str, dict[str, tuple[str, str]]] = {

    # -----------------------------------------------------------------------
    # AWS
    # -----------------------------------------------------------------------
    "aws": {
        # Compute
        "ec2": ("compute", "EC2"),
        "ec2_instance": ("compute", "EC2"),
        "instance": ("compute", "EC2"),
        "lambda": ("compute", "Lambda"),
        "lambda_function": ("compute", "Lambda"),
        "ecs": ("compute", "ECS"),
        "ecs_cluster": ("compute", "ElasticContainerService"),
        "ecs_service": ("compute", "ElasticContainerServiceService"),
        "ecs_task_definition": ("compute", "ElasticContainerServiceTask"),
        "eks": ("compute", "EKS"),
        "eks_cluster": ("compute", "ElasticKubernetesService"),
        "ecr": ("compute", "ECR"),
        "ecr_repository": ("compute", "EC2ContainerRegistry"),
        "fargate": ("compute", "Fargate"),
        "batch": ("compute", "Batch"),
        "batch_job_definition": ("compute", "Batch"),
        "batch_compute_environment": ("compute", "Batch"),
        "elasticbeanstalk": ("compute", "ElasticBeanstalk"),
        "elastic_beanstalk_application": ("compute", "ElasticBeanstalkApplication"),
        "lightsail": ("compute", "Lightsail"),
        "app_runner_service": ("compute", "AppRunner"),
        "autoscaling_group": ("compute", "EC2AutoScaling"),
        "launch_configuration": ("compute", "EC2"),
        "launch_template": ("compute", "EC2"),
        "spot_instance_request": ("compute", "EC2SpotInstance"),
        # Storage
        "s3": ("storage", "SimpleStorageServiceS3"),
        "s3_bucket": ("storage", "SimpleStorageServiceS3"),
        "s3_bucket_policy": ("storage", "SimpleStorageServiceS3"),
        "s3_bucket_object": ("storage", "SimpleStorageServiceS3Object"),
        "s3_object": ("storage", "SimpleStorageServiceS3Object"),
        "ebs": ("storage", "ElasticBlockStoreEBS"),
        "ebs_volume": ("storage", "ElasticBlockStoreEBSVolume"),
        "ebs_snapshot": ("storage", "ElasticBlockStoreEBSSnapshot"),
        "efs": ("storage", "EFS"),
        "efs_file_system": ("storage", "ElasticFileSystemEFS"),
        "efs_mount_target": ("storage", "ElasticFileSystemEFS"),
        "fsx": ("storage", "FSx"),
        "fsx_windows_file_system": ("storage", "FsxForWindowsFileServer"),
        "fsx_lustre_file_system": ("storage", "FsxForLustre"),
        "storage_gateway": ("storage", "StorageGateway"),
        "storagegateway_gateway": ("storage", "StorageGateway"),
        "backup": ("storage", "Backup"),
        "backup_plan": ("storage", "Backup"),
        "backup_vault": ("storage", "Backup"),
        "glacier": ("storage", "S3Glacier"),
        "glacier_vault": ("storage", "S3GlacierVault"),
        # Database
        "rds": ("database", "RDS"),
        "rds_instance": ("database", "RDS"),
        "rds_cluster": ("database", "Aurora"),
        "db_instance": ("database", "RDS"),
        "db_cluster": ("database", "Aurora"),
        "aurora": ("database", "Aurora"),
        "dynamodb": ("database", "Dynamodb"),
        "dynamodb_table": ("database", "DynamodbTable"),
        "dynamodb_global_table": ("database", "Dynamodb"),
        "neptune": ("database", "Neptune"),
        "neptune_cluster": ("database", "Neptune"),
        "neptune_instance": ("database", "Neptune"),
        "redshift": ("database", "Redshift"),
        "redshift_cluster": ("database", "Redshift"),
        "elasticache": ("database", "Elasticache"),
        "elasticache_cluster": ("database", "Elasticache"),
        "elasticache_replication_group": ("database", "ElasticacheForRedis"),
        "elasticache_subnet_group": ("database", "Elasticache"),
        "documentdb": ("database", "DocumentDB"),
        "documentdb_cluster": ("database", "DocumentDB"),
        "timestream": ("database", "Timestream"),
        "timestream_database": ("database", "Timestream"),
        "timestream_table": ("database", "Timestream"),
        "keyspaces": ("database", "KeyspacesManagedApacheCassandraService"),
        "qldb": ("database", "QLDB"),
        "qldb_ledger": ("database", "QuantumLedgerDatabaseQldb"),
        "dax": ("database", "DynamodbDax"),
        "dax_cluster": ("database", "DynamodbDax"),
        # Analytics
        "glue": ("analytics", "Glue"),
        "glue_job": ("analytics", "Glue"),
        "glue_crawler": ("analytics", "GlueCrawlers"),
        "glue_catalog_database": ("analytics", "GlueDataCatalog"),
        "glue_catalog_table": ("analytics", "GlueDataCatalog"),
        "athena": ("analytics", "Athena"),
        "athena_workgroup": ("analytics", "Athena"),
        "athena_database": ("analytics", "Athena"),
        "emr": ("analytics", "EMR"),
        "emr_cluster": ("analytics", "EMRCluster"),
        "kinesis": ("analytics", "Kinesis"),
        "kinesis_stream": ("analytics", "KinesisDataStreams"),
        "kinesis_firehose_delivery_stream": ("analytics", "KinesisDataFirehose"),
        "kinesis_analytics_application": ("analytics", "KinesisDataAnalytics"),
        "kinesis_video_stream": ("analytics", "KinesisVideoStreams"),
        "quicksight": ("analytics", "Quicksight"),
        "datapipeline": ("analytics", "DataPipeline"),
        "data_pipeline": ("analytics", "DataPipeline"),
        "lakeformation": ("analytics", "LakeFormation"),
        "lake_formation_data_lake_settings": ("analytics", "LakeFormation"),
        "msk": ("analytics", "ManagedStreamingForKafka"),
        "msk_cluster": ("analytics", "ManagedStreamingForKafka"),
        "opensearch": ("analytics", "AmazonOpensearchService"),
        "opensearch_domain": ("analytics", "AmazonOpensearchService"),
        "elasticsearch": ("analytics", "ElasticsearchService"),
        "elasticsearch_domain": ("analytics", "ElasticsearchService"),
        # ML
        "sagemaker": ("ml", "Sagemaker"),
        "sagemaker_endpoint": ("ml", "Sagemaker"),
        "sagemaker_model": ("ml", "SagemakerModel"),
        "sagemaker_notebook_instance": ("ml", "SagemakerNotebook"),
        "sagemaker_training_job": ("ml", "SagemakerTrainingJob"),
        "comprehend": ("ml", "Comprehend"),
        "rekognition": ("ml", "Rekognition"),
        "textract": ("ml", "Textract"),
        "translate": ("ml", "Translate"),
        "transcribe": ("ml", "Transcribe"),
        "polly": ("ml", "Polly"),
        "forecast": ("ml", "Forecast"),
        "personalize": ("ml", "Personalize"),
        "lex": ("ml", "Lex"),
        "lex_bot": ("ml", "Lex"),
        "bedrock": ("ml", "Bedrock"),
        "kendra": ("ml", "Kendra"),
        "kendra_index": ("ml", "Kendra"),
        # Network
        "vpc": ("network", "VPC"),
        "subnet": ("network", "PrivateSubnet"),
        "internet_gateway": ("network", "InternetGateway"),
        "nat_gateway": ("network", "NATGateway"),
        "route": ("network", "RouteTable"),
        "route_table": ("network", "RouteTable"),
        "route_table_association": ("network", "RouteTable"),
        "gateway": ("network", "InternetGateway"),
        "elb": ("network", "ELB"),
        "alb": ("network", "ALB"),
        "nlb": ("network", "NLB"),
        "lb": ("network", "ElasticLoadBalancing"),
        "lb_listener": ("network", "ElasticLoadBalancing"),
        "lb_target_group": ("network", "ElasticLoadBalancing"),
        "alb_listener": ("network", "ALB"),
        "alb_target_group": ("network", "ALB"),
        "cloudfront": ("network", "CloudFront"),
        "cloudfront_distribution": ("network", "CloudFront"),
        "route53": ("network", "Route53"),
        "route53_record": ("network", "Route53"),
        "route53_zone": ("network", "Route53HostedZone"),
        "route53_health_check": ("network", "Route53"),
        "apigateway": ("network", "APIGateway"),
        "api_gateway": ("network", "APIGateway"),
        "api_gateway_rest_api": ("network", "APIGateway"),
        "api_gateway_v2_api": ("network", "APIGateway"),
        "api_gateway_stage": ("network", "APIGateway"),
        "apigatewayv2": ("network", "APIGateway"),
        "cloudmap": ("network", "CloudMap"),
        "service_discovery_service": ("network", "CloudMap"),
        "appmesh": ("network", "AppMesh"),
        "appmesh_mesh": ("network", "AppMesh"),
        "globalaccelerator": ("network", "GlobalAccelerator"),
        "global_accelerator": ("network", "GlobalAccelerator"),
        "transit_gateway": ("network", "TransitGateway"),
        "transitgateway": ("network", "TransitGateway"),
        "transit_gateway_attachment": ("network", "TransitGatewayAttachment"),
        "vpn_gateway": ("network", "VpnGateway"),
        "vpn_connection": ("network", "VpnConnection"),
        "direct_connect": ("network", "DirectConnect"),
        "dx_connection": ("network", "DirectConnect"),
        "network_firewall": ("network", "NetworkFirewall"),
        "networkfirewall": ("network", "NetworkFirewall"),
        "network_acl": ("network", "Nacl"),
        "nacl": ("network", "Nacl"),
        "vpc_peering_connection": ("network", "VPCPeering"),
        "vpc_endpoint": ("network", "Privatelink"),
        "vpc_endpoint_service": ("network", "Privatelink"),
        "eip": ("compute", "EC2ElasticIpAddress"),
        "elastic_ip": ("compute", "EC2ElasticIpAddress"),
        "security_group": ("network", "Nacl"),
        "security_group_rule": ("network", "Nacl"),
        "client_vpn_endpoint": ("network", "ClientVpn"),
        # Security
        "iam": ("security", "IAM"),
        "iam_role": ("security", "IAMRole"),
        "iam_user": ("security", "IAM"),
        "iam_group": ("security", "IAM"),
        "iam_policy": ("security", "IAMPermissions"),
        "iam_instance_profile": ("security", "IAM"),
        "iam_access_analyzer": ("security", "IAMAccessAnalyzer"),
        "kms": ("security", "KMS"),
        "kms_key": ("security", "KeyManagementService"),
        "kms_alias": ("security", "KeyManagementService"),
        "secretsmanager": ("security", "SecretsManager"),
        "secretsmanager_secret": ("security", "SecretsManager"),
        "secrets_manager_secret": ("security", "SecretsManager"),
        "cloudtrail": ("management", "Cloudtrail"),
        "cloudtrail_trail": ("management", "Cloudtrail"),
        "guardduty": ("security", "Guardduty"),
        "guardduty_detector": ("security", "Guardduty"),
        "waf": ("security", "WAF"),
        "wafv2": ("security", "WAF"),
        "wafv2_web_acl": ("security", "WAF"),
        "waf_web_acl": ("security", "WAF"),
        "shield": ("security", "Shield"),
        "shield_protection": ("security", "ShieldAdvanced"),
        "inspector": ("security", "Inspector"),
        "inspector2_enabler": ("security", "Inspector"),
        "macie": ("security", "Macie"),
        "macie2_account": ("security", "Macie"),
        "security_hub": ("security", "SecurityHub"),
        "securityhub_account": ("security", "SecurityHub"),
        "cognito": ("security", "Cognito"),
        "cognito_user_pool": ("security", "Cognito"),
        "cognito_identity_pool": ("security", "Cognito"),
        "acm": ("security", "ACM"),
        "acm_certificate": ("security", "CertificateManager"),
        "acmpca_certificate_authority": ("security", "CertificateAuthority"),
        "organizations": ("management", "Organizations"),
        "organizations_account": ("management", "Organizations"),
        "ram": ("security", "RAM"),
        "ram_resource_share": ("security", "ResourceAccessManager"),
        "sso": ("security", "SingleSignOn"),
        "detective": ("security", "Detective"),
        "firewallmanager": ("security", "FirewallManager"),
        "cloudhsm": ("security", "Cloudhsm"),
        # Management
        "cloudwatch": ("management", "Cloudwatch"),
        "cloudwatch_log_group": ("management", "CloudwatchLogs"),
        "cloudwatch_metric_alarm": ("management", "CloudwatchAlarm"),
        "cloudwatch_event_rule": ("management", "Cloudwatch"),
        "cloudwatch_dashboard": ("management", "Cloudwatch"),
        "cloudwatchlogs": ("management", "CloudwatchLogs"),
        "cloudwatch_log_metric_filter": ("management", "CloudwatchLogs"),
        "cloudformation": ("management", "Cloudformation"),
        "cloudformation_stack": ("management", "CloudformationStack"),
        "ssm": ("management", "SSM"),
        "ssm_parameter": ("management", "SystemsManagerParameterStore"),
        "ssm_document": ("management", "SystemsManagerDocuments"),
        "trustedadvisor": ("management", "TrustedAdvisor"),
        "servicecatalog": ("management", "ServiceCatalog"),
        "servicecatalog_portfolio": ("management", "ServiceCatalog"),
        "controltower": ("management", "ControlTower"),
        "config": ("management", "Config"),
        "config_rule": ("management", "Config"),
        "organizations_policy": ("management", "Organizations"),
        "budgets": ("management", "ManagementConsole"),
        "cost_explorer": ("management", "ManagementConsole"),
        "proton": ("management", "Proton"),
        # Integration
        "sqs": ("integration", "SQS"),
        "sqs_queue": ("integration", "SimpleQueueServiceSqs"),
        "sns": ("integration", "SNS"),
        "sns_topic": ("integration", "SimpleNotificationServiceSns"),
        "eventbridge": ("integration", "Eventbridge"),
        "cloudwatch_event_target": ("integration", "Eventbridge"),
        "eventbridge_rule": ("integration", "EventbridgeRule"),
        "eventbridge_event_bus": ("integration", "EventbridgeCustomEventBusResource"),
        "sfn": ("integration", "SF"),
        "sfn_state_machine": ("integration", "StepFunctions"),
        "stepfunctions": ("integration", "StepFunctions"),
        "mq": ("integration", "MQ"),
        "mq_broker": ("integration", "MQ"),
        "appsync": ("integration", "Appsync"),
        "appsync_graphql_api": ("integration", "Appsync"),
        # DevTools
        "codebuild": ("devtools", "Codebuild"),
        "codebuild_project": ("devtools", "Codebuild"),
        "codecommit": ("devtools", "Codecommit"),
        "codecommit_repository": ("devtools", "Codecommit"),
        "codepipeline": ("devtools", "Codepipeline"),
        "codedeploy": ("devtools", "Codedeploy"),
        "codedeploy_app": ("devtools", "Codedeploy"),
        "codeartifact": ("devtools", "Codeartifact"),
        "codeartifact_domain": ("devtools", "Codeartifact"),
        "xray": ("management", "Cloudwatch"),
    },

    # -----------------------------------------------------------------------
    # Azure
    # -----------------------------------------------------------------------
    "azure": {
        # Compute
        "virtual_machine": ("compute", "VirtualMachine"),
        "linux_virtual_machine": ("compute", "VirtualMachine"),
        "windows_virtual_machine": ("compute", "VirtualMachine"),
        "virtual_machine_scale_set": ("compute", "VMScaleSet"),
        "function_app": ("compute", "FunctionApps"),
        "linux_function_app": ("compute", "FunctionApps"),
        "windows_function_app": ("compute", "FunctionApps"),
        "app_service": ("compute", "AppServices"),
        "linux_web_app": ("compute", "AppServices"),
        "windows_web_app": ("compute", "AppServices"),
        "app_service_plan": ("appservices", "AppServicePlans"),
        "container_group": ("compute", "ContainerInstances"),
        "container_registry": ("compute", "ContainerRegistries"),
        "container_app": ("compute", "ContainerApps"),
        "kubernetes_cluster": ("compute", "KubernetesServices"),
        "batch_account": ("compute", "BatchAccounts"),
        "spring_cloud_service": ("compute", "AzureSpringApps"),
        # Storage
        "storage_account": ("storage", "StorageAccounts"),
        "storage_blob": ("storage", "BlobStorage"),
        "storage_container": ("storage", "BlobStorage"),
        "storage_share": ("storage", "AzureFileshares"),
        "storage_table": ("storage", "TableStorage"),
        "storage_queue": ("storage", "QueuesStorage"),
        "managed_disk": ("compute", "Disks"),
        "data_lake_store": ("storage", "DataLakeStorage"),
        "data_lake_gen2_path": ("storage", "DataLakeStorage"),
        "recovery_services_vault": ("storage", "RecoveryServicesVaults"),
        # Database
        "mssql_server": ("database", "SQLServers"),
        "mssql_database": ("database", "SQLDatabases"),
        "sql_server": ("database", "SQLServers"),
        "sql_database": ("database", "SQLDatabases"),
        "cosmosdb_account": ("database", "CosmosDb"),
        "cosmosdb_sql_database": ("database", "CosmosDb"),
        "postgresql_server": ("database", "DatabaseForPostgresqlServers"),
        "postgresql_flexible_server": ("database", "DatabaseForPostgresqlServers"),
        "mysql_server": ("database", "DatabaseForMysqlServers"),
        "mysql_flexible_server": ("database", "DatabaseForMysqlServers"),
        "mariadb_server": ("database", "DatabaseForMariadbServers"),
        "redis_cache": ("database", "CacheForRedis"),
        "synapse_workspace": ("database", "SynapseAnalytics"),
        "sql_managed_instance": ("database", "SQLManagedInstances"),
        "elasticsearch_cluster": ("database", "ElasticJobAgents"),
        # Integration
        "service_bus_namespace": ("integration", "ServiceBus"),
        "service_bus_queue": ("integration", "ServiceBus"),
        "service_bus_topic": ("integration", "ServiceBus"),
        "eventhub_namespace": ("integration", "PartnerNamespace"),
        "eventhub": ("integration", "PartnerNamespace"),
        "event_grid_topic": ("integration", "EventGridTopics"),
        "event_grid_domain": ("integration", "EventGridDomains"),
        "event_grid_event_subscription": ("integration", "EventGridSubscriptions"),
        "api_management": ("integration", "APIManagement"),
        "logic_app_workflow": ("integration", "LogicApps"),
        "logic_app_action_http": ("integration", "LogicApps"),
        "notification_hub_namespace": ("integration", "PartnerNamespace"),
        # Network
        "virtual_network": ("network", "VirtualNetworks"),
        "subnet": ("network", "Subnets"),
        "network_interface": ("network", "NetworkInterfaces"),
        "public_ip": ("network", "PublicIpAddresses"),
        "public_ip_prefix": ("network", "PublicIpAddresses"),
        "lb": ("network", "LoadBalancers"),
        "lb_backend_address_pool": ("network", "LoadBalancers"),
        "lb_rule": ("network", "LoadBalancers"),
        "lb_probe": ("network", "LoadBalancers"),
        "application_gateway": ("network", "ApplicationGateway"),
        "cdn_profile": ("network", "CDNProfiles"),
        "cdn_endpoint": ("network", "CDNProfiles"),
        "frontdoor": ("network", "FrontDoors"),
        "frontdoor_firewall_policy": ("network", "FrontDoors"),
        "traffic_manager_profile": ("network", "TrafficManagerProfiles"),
        "traffic_manager_endpoint": ("network", "TrafficManagerProfiles"),
        "dns_zone": ("network", "DNSZones"),
        "dns_a_record": ("network", "DNSZones"),
        "dns_cname_record": ("network", "DNSZones"),
        "private_dns_zone": ("network", "DNSPrivateZones"),
        "network_security_group": ("network", "NetworkSecurityGroupsClassic"),
        "network_security_rule": ("network", "NetworkSecurityGroupsClassic"),
        "virtual_network_gateway": ("network", "VirtualNetworkGateways"),
        "local_network_gateway": ("network", "LocalNetworkGateways"),
        "virtual_network_peering": ("network", "VirtualNetworks"),
        "route_table": ("network", "RouteTables"),
        "route": ("network", "RouteTables"),
        "firewall": ("network", "Firewall"),
        "firewall_policy": ("network", "Firewall"),
        "private_endpoint": ("network", "PrivateEndpoint"),
        "express_route_circuit": ("network", "ExpressrouteCircuits"),
        "nat_gateway": ("network", "PublicIpAddresses"),
        "bastion_host": ("network", "VirtualNetworkGateways"),
        "network_watcher": ("network", "NetworkWatcher"),
        "web_application_firewall_policy": ("network", "ApplicationGateway"),
        # Security / Identity
        "key_vault": ("security", "KeyVaults"),
        "key_vault_secret": ("security", "KeyVaults"),
        "key_vault_certificate": ("security", "KeyVaults"),
        "role_assignment": ("identity", "ManagedIdentities"),
        "user_assigned_identity": ("identity", "ManagedIdentities"),
        "active_directory_domain_service": ("identity", "AzureADDomainServices"),
        # Management / Monitoring
        "monitor_action_group": ("compute", "AppServices"),
        "log_analytics_workspace": ("compute", "AppServices"),
        "application_insights": ("web", "AppServices"),
        "automation_account": ("compute", "AppServices"),
        # Analytics / AI
        "data_factory": ("database", "DataFactory"),
        "synapse_sql_pool": ("database", "SynapseAnalytics"),
        "stream_analytics_job": ("database", "SynapseAnalytics"),
        "machine_learning_workspace": ("compute", "AppServices"),
        "cognitive_account": ("web", "CognitiveServices"),
        "search_service": ("web", "CognitiveSearch"),
        "databricks_workspace": ("compute", "AppServices"),
        "hdinsight_hadoop_cluster": ("compute", "AppServices"),
        # IoT
        "iothub": ("integration", "APIConnections"),
        "eventhub_consumer_group": ("integration", "EventGridSubscriptions"),
    },

    # -----------------------------------------------------------------------
    # GCP
    # -----------------------------------------------------------------------
    "gcp": {
        # Compute
        "compute_instance": ("compute", "ComputeEngine"),
        "compute_instance_template": ("compute", "ComputeEngine"),
        "compute_instance_group": ("compute", "ComputeEngine"),
        "compute_instance_group_manager": ("compute", "ComputeEngine"),
        "compute_autoscaler": ("compute", "ComputeEngine"),
        "container_cluster": ("compute", "GKE"),
        "container_node_pool": ("compute", "GKE"),
        "cloud_run_service": ("compute", "Run"),
        "cloud_run_v2_service": ("compute", "Run"),
        "cloud_run_v2_job": ("compute", "Run"),
        "cloudfunctions_function": ("compute", "Functions"),
        "cloudfunctions2_function": ("compute", "Functions"),
        "app_engine_application": ("compute", "AppEngine"),
        "app_engine_service": ("compute", "AppEngine"),
        "app_engine_standard_app_version": ("compute", "AppEngine"),
        # Storage
        "storage_bucket": ("storage", "GCS"),
        "storage_bucket_object": ("storage", "GCS"),
        "filestore_instance": ("storage", "Filestore"),
        "filestore_snapshot": ("storage", "Filestore"),
        "compute_disk": ("storage", "PersistentDisk"),
        "compute_snapshot": ("storage", "PersistentDisk"),
        # Database
        "sql_database_instance": ("database", "SQL"),
        "sql_database": ("database", "SQL"),
        "sql_user": ("database", "SQL"),
        "bigtable_instance": ("database", "Bigtable"),
        "bigtable_table": ("database", "Bigtable"),
        "spanner_instance": ("database", "Spanner"),
        "spanner_database": ("database", "Spanner"),
        "firestore_database": ("database", "Firestore"),
        "firestore_document": ("database", "Firestore"),
        "datastore_index": ("database", "Datastore"),
        "redis_instance": ("database", "Memorystore"),
        "alloydb_cluster": ("database", "SQL"),
        "alloydb_instance": ("database", "SQL"),
        # Analytics / Stream
        "pubsub_topic": ("analytics", "PubSub"),
        "pubsub_subscription": ("analytics", "PubSub"),
        "pubsub_schema": ("analytics", "PubSub"),
        "bigquery_dataset": ("analytics", "Bigquery"),
        "bigquery_table": ("analytics", "Bigquery"),
        "bigquery_job": ("analytics", "Bigquery"),
        "bigquery_data_transfer_config": ("analytics", "Bigquery"),
        "dataflow_job": ("analytics", "Dataflow"),
        "dataflow_flex_template_job": ("analytics", "Dataflow"),
        "dataproc_cluster": ("analytics", "Dataproc"),
        "dataproc_job": ("analytics", "Dataproc"),
        "composer_environment": ("analytics", "Composer"),
        "data_catalog_entry_group": ("analytics", "DataCatalog"),
        "datafusion_instance": ("analytics", "DataFusion"),
        "looker_instance": ("analytics", "Looker"),
        # ML
        "vertex_ai_dataset": ("ml", "VertexAI"),
        "vertex_ai_endpoint": ("ml", "VertexAI"),
        "vertex_ai_model": ("ml", "VertexAI"),
        "ml_engine_model": ("ml", "AIPlatform"),
        "dialogflow_agent": ("ml", "AIPlatform"),
        "dialogflow_cx_agent": ("ml", "AIPlatform"),
        # Network
        "compute_network": ("network", "VirtualPrivateCloud"),
        "compute_subnetwork": ("network", "VPC"),
        "compute_router": ("network", "Router"),
        "compute_vpn_gateway": ("network", "VPN"),
        "compute_vpn_tunnel": ("network", "VPN"),
        "compute_forwarding_rule": ("network", "LoadBalancing"),
        "compute_global_forwarding_rule": ("network", "LoadBalancing"),
        "compute_backend_service": ("network", "LoadBalancing"),
        "compute_target_https_proxy": ("network", "LoadBalancing"),
        "compute_url_map": ("network", "LoadBalancing"),
        "compute_firewall": ("network", "FirewallRules"),
        "compute_global_address": ("network", "ExternalIpAddresses"),
        "compute_address": ("network", "ExternalIpAddresses"),
        "compute_nat": ("network", "NAT"),
        "compute_interconnect_attachment": ("network", "DedicatedInterconnect"),
        "compute_security_policy": ("network", "Armor"),
        "dns_managed_zone": ("network", "DNS"),
        "dns_record_set": ("network", "DNS"),
        "network_services_edge_cache_service": ("network", "CDN"),
        "compute_ssl_certificate": ("network", "NetworkSecurity"),
        "compute_backend_bucket": ("storage", "GCS"),
        "compute_http_health_check": ("network", "LoadBalancing"),
        "compute_https_health_check": ("network", "LoadBalancing"),
        # DevOps / Tools
        "cloud_tasks_queue": ("devtools", "Tasks"),
        "cloud_scheduler_job": ("devtools", "Scheduler"),
        "eventarc_trigger": ("devtools", "Build"),
        "container_registry": ("devtools", "ContainerRegistry"),
        "artifact_registry_repository": ("devtools", "ContainerRegistry"),
        "sourcerepo_repository": ("devtools", "SourceRepositories"),
        "cloudbuild_trigger": ("devtools", "Build"),
        "project": ("compute", "ComputeEngine"),
        # Security
        "kms_key_ring": ("devtools", "SDK"),
        "kms_crypto_key": ("devtools", "SDK"),
        "secret_manager_secret": ("devtools", "SDK"),
        "iam_service_account": ("network", "VirtualPrivateCloud"),
        "iam_member": ("network", "VirtualPrivateCloud"),
        "apigee_organization": ("devtools", "SDK"),
        "endpoints_service": ("devtools", "SDK"),
        "cloud_run_domain_mapping": ("network", "DNS"),
    },
}

# ---------------------------------------------------------------------------
# Step 4: Fuzzy matching fallback – for types NOT in curated rules
# ---------------------------------------------------------------------------

def _normalize(s: str) -> str:
    """Lowercase, strip underscores/hyphens for fuzzy matching."""
    return re.sub(r"[_\-\s]", "", s).lower()


def _fuzzy_match_class(
    target: str,
    index: dict[str, list[str]],
    provider: str,
) -> tuple[str, str] | None:
    """Find best (module, ClassName) by fuzzy matching target against index."""
    target_norm = _normalize(target)
    if not target_norm:
        return None

    best_score = 0
    best: tuple[str, str] | None = None

    for module, classes in index.items():
        for cls in classes:
            cls_norm = _normalize(cls)
            # Substring match: class name contains target or vice-versa
            if target_norm in cls_norm or cls_norm in target_norm:
                score = min(len(target_norm), len(cls_norm))
                if score > best_score:
                    best_score = score
                    best = (module, cls)

    return best


# ---------------------------------------------------------------------------
# Step 5: Build complete mappings for a provider
# ---------------------------------------------------------------------------

def _build_provider_mappings(
    provider: str,
    index: dict[str, list[str]],
    existing: dict[str, dict],
    force: bool,
) -> dict[str, dict]:
    """Build the final mappings dict for one provider."""
    curated = CURATED_RULES.get(provider, {})
    result: dict[str, dict] = {}

    # 1. Apply curated rules (verified against library index)
    added_curated = 0
    invalid_curated = 0
    for tf_key, (module, cls) in curated.items():
        if _class_exists(provider, module, cls):
            result[tf_key] = {
                "category": module,
                "class": cls,
                "description": _make_description(tf_key),
                "source": "curated",
            }
            added_curated += 1
        else:
            # Class no longer exists – try fuzzy fallback
            print(f"    [WARN] {provider}.{module}.{cls} missing → fuzzy fallback for {tf_key}")
            match = _fuzzy_match_class(cls, index, provider)
            if match:
                m, c = match
                result[tf_key] = {
                    "category": m,
                    "class": c,
                    "description": _make_description(tf_key),
                    "source": "curated-fallback",
                }
            invalid_curated += 1

    print(f"    Curated: {added_curated} valid, {invalid_curated} needed fallback")

    # 2. Preserve existing custom entries not in curated list
    for tf_key, entry in existing.items():
        if tf_key not in result:
            cat = entry.get("category", "")
            cls = entry.get("class", "")
            if cat and cls and _class_exists(provider, cat, cls):
                entry["source"] = "preserved"
                result[tf_key] = entry
            else:
                print(f"    [STALE] Removing stale entry: {tf_key} → {cat}.{cls}")

    # 3. Detect NEW classes in the library not covered by any mapping
    covered_classes: set[str] = {v["class"] for v in result.values()}
    new_discoveries: list[tuple[str, str, str]] = []
    for module, classes in index.items():
        for cls in classes:
            if cls not in covered_classes:
                new_discoveries.append((module, cls, cls))

    if new_discoveries:
        print(f"    [NEW] {len(new_discoveries)} library classes not yet mapped:")
        for mod, cls, _ in sorted(new_discoveries)[:20]:
            print(f"      diagrams.{provider}.{mod}.{cls}")
        if len(new_discoveries) > 20:
            print(f"      … and {len(new_discoveries) - 20} more")

    # 4. Clean up internal "source" field for output
    clean: dict[str, dict] = {}
    for k, v in result.items():
        clean[k] = {
            "category": v["category"],
            "class": v["class"],
            "description": v["description"],
        }

    return clean


def _make_description(tf_key: str) -> str:
    """Generate a human-readable description from the Terraform key."""
    return " ".join(w.capitalize() for w in tf_key.replace("_", " ").split())


# ---------------------------------------------------------------------------
# Step 6: Main entry point
# ---------------------------------------------------------------------------

def load_existing(path: Path) -> dict[str, dict]:
    """Load the existing mappings file if present."""
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def run(dry_run: bool = False, force: bool = False) -> None:
    print("=" * 70)
    print("  Intelligent Service Mappings Updater")
    print("=" * 70)

    # 1. Introspect library
    print("\n[1] Introspecting diagrams library …")
    lib_index = introspect_all()

    # 2. Load existing mappings
    print("\n[2] Loading existing mappings …")
    existing_all = load_existing(OUTPUT_FILE)
    print(f"  Found {sum(len(v) for v in existing_all.values())} existing entries across {len(existing_all)} providers")

    # 3. Build new mappings per provider
    print("\n[3] Building verified mappings …")
    new_mappings: dict[str, dict] = {}
    for provider in PROVIDERS:
        if provider not in lib_index or not lib_index[provider]:
            print(f"  [SKIP] {provider} – no modules found")
            continue
        print(f"\n  Provider: {provider}")
        existing_prov = existing_all.get(provider, {}) if not force else {}
        new_mappings[provider] = _build_provider_mappings(
            provider,
            lib_index[provider],
            existing_prov,
            force,
        )
        print(f"    → {len(new_mappings[provider])} total entries")

    # 4. Diff summary
    print("\n[4] Change summary …")
    for provider in PROVIDERS:
        old = set(existing_all.get(provider, {}).keys())
        new = set(new_mappings.get(provider, {}).keys())
        added = new - old
        removed = old - new
        changed = {
            k for k in (new & old)
            if new_mappings[provider][k] != existing_all.get(provider, {}).get(k)
        }
        print(f"  {provider:8s}: +{len(added):3d} added | -{len(removed):3d} removed | ~{len(changed):3d} changed")
        for k in sorted(added)[:10]:
            print(f"             + {k} → {new_mappings[provider][k]['class']}")
        for k in sorted(removed):
            print(f"             - {k}")
        for k in sorted(changed)[:10]:
            old_cls = existing_all.get(provider, {}).get(k, {}).get("class", "?")
            new_cls = new_mappings[provider][k]["class"]
            if old_cls != new_cls:
                print(f"             ~ {k}: {old_cls} → {new_cls}")

    # 5. Write
    if dry_run:
        print("\n[DRY RUN] No files written.")
    else:
        print(f"\n[5] Writing {OUTPUT_FILE} …")
        with open(OUTPUT_FILE, "w") as f:
            json.dump(new_mappings, f, indent=2, sort_keys=True)
            f.write("\n")
        total = sum(len(v) for v in new_mappings.values())
        print(f"  Done. {total} entries written for {len(new_mappings)} providers.")

    print("\n" + "=" * 70)
    print("  Complete!")
    print("=" * 70)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Regenerate comprehensive_service_mappings.json from the installed diagrams library."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing the file",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore existing entries and rebuild from scratch",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run, force=args.force)
