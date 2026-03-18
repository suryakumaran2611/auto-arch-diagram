#!/usr/bin/env python3
"""Verify critical icon mappings are correct after update."""
import json

m = json.load(open("tools/comprehensive_service_mappings.json"))

checks = [
    ("aws", "subnet", "PrivateSubnet"),
    ("aws", "nat_gateway", "NATGateway"),
    ("aws", "internet_gateway", "InternetGateway"),
    ("aws", "wafv2_web_acl", "WAF"),
    ("aws", "security_group", "Nacl"),
    ("aws", "elasticsearch_domain", "ElasticsearchService"),
    ("azure", "storage_account", "StorageAccounts"),
    ("azure", "virtual_network", "VirtualNetworks"),
    ("azure", "kubernetes_cluster", "KubernetesServices"),
    ("azure", "cosmosdb_account", "CosmosDb"),
    ("gcp", "pubsub_topic", "PubSub"),
    ("gcp", "sql_database_instance", "SQL"),
    ("gcp", "dns_managed_zone", "DNS"),
]

print("=== Critical Mapping Verification ===\n")
failed = []
for provider, key, expected_class in checks:
    entry = m.get(provider, {}).get(key, {})
    actual = entry.get("class", "MISSING")
    ok = actual == expected_class
    status = "OK  " if ok else "FAIL"
    print(f"  [{status}] {provider}.{key} → {actual}  (expected: {expected_class})")
    if not ok:
        failed.append((provider, key, expected_class, actual))

print(f"\nTotal: {len(checks)} checks, {len(failed)} failures")
if failed:
    print("\nFailed mappings:")
    for p, k, e, a in failed:
        print(f"  {p}.{k}: expected {e}, got {a}")
