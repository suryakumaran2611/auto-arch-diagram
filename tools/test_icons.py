#!/usr/bin/env python3
"""Test icon mappings for AWS, Azure, GCP resources."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generate_arch_diagram import _icon_class_for

tests = [
    # AWS
    "aws_lambda_function",
    "aws_vpc",
    "aws_subnet",
    "aws_internet_gateway",
    "aws_nat_gateway",
    "aws_api_gateway_rest_api",
    "aws_cloudwatch_log_group",
    "aws_elasticsearch_domain",
    "aws_glue_job",
    "aws_s3_bucket",
    "aws_rds_instance",
    "aws_dynamodb_table",
    "aws_sqs_queue",
    "aws_sns_topic",
    "aws_ecs_service",
    "aws_eks_cluster",
    "aws_cloudfront_distribution",
    "aws_route53_record",
    "aws_wafv2_web_acl",
    "aws_kms_key",
    "aws_secretsmanager_secret",
    "aws_iam_role",
    "aws_security_group",
    "aws_alb",
    "aws_elasticache_cluster",
    # Azure
    "azurerm_virtual_network",
    "azurerm_subnet",
    "azurerm_virtual_machine",
    "azurerm_function_app",
    "azurerm_storage_account",
    "azurerm_sql_database",
    "azurerm_app_service",
    "azurerm_kubernetes_cluster",
    "azurerm_api_management",
    "azurerm_key_vault",
    "azurerm_application_gateway",
    "azurerm_cosmosdb_account",
    "azurerm_service_bus_namespace",
    "azurerm_eventhub_namespace",
    "azurerm_public_ip",
    "azurerm_network_interface",
    "azurerm_resource_group",
    # GCP
    "google_compute_instance",
    "google_container_cluster",
    "google_storage_bucket",
    "google_sql_database_instance",
    "google_cloudfunctions_function",
    "google_pubsub_topic",
    "google_compute_network",
    "google_compute_subnetwork",
    "google_bigquery_dataset",
    "google_compute_firewall",
    "google_compute_forwarding_rule",
    "google_dns_managed_zone",
    "google_compute_global_address",
    "google_cloud_run_service",
    "google_composer_environment",
]

print("=" * 80)
print("ICON MAPPING TEST RESULTS")
print("=" * 80)

missing = []
found = []
for t in tests:
    result = _icon_class_for(t)
    if result is None:
        missing.append(t)
        print(f"MISSING: {t}")
    else:
        found.append(t)
        # Only show short name
        cls_name = getattr(result, '__name__', str(result))
        print(f"OK:      {t} -> {cls_name}")

print()
print("=" * 80)
print(f"FOUND:   {len(found)}/{len(tests)}")
print(f"MISSING: {len(missing)}/{len(tests)}")
if missing:
    print()
    print("MISSING ICONS:")
    for m in missing:
        print(f"  - {m}")
