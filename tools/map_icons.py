#!/usr/bin/env python3
"""
Helper script to create a mapping between downloaded cloud provider icons
and Terraform resource type naming conventions.

This script scans the icons/ directories and suggests icon mappings for
common Terraform resources that may not be available in the diagrams library.
"""

import json
from pathlib import Path
from typing import Dict, List

# Common Terraform resource types that need custom icons
TERRAFORM_RESOURCES = {
    "aws": [
        "aws_amplify_app",
        "aws_app_runner_service",
        "aws_apprunner_service",
        "aws_lightsail_instance",
        "aws_elasticache_cluster",
        "aws_elasticache_replication_group",
        "aws_mq_broker",
        "aws_neptune_cluster",
        "aws_qldb_ledger",
        "aws_timestreamwrite_database",
        "aws_backup_vault",
        "aws_fsx_windows_file_system",
        "aws_datasync_task",
        "aws_transfer_server",
    ],
    "azure": [
        "azurerm_static_web_app",
        "azurerm_static_site",
        "azurerm_container_app",
        "azurerm_container_app_environment",
        "azurerm_spring_cloud_service",
        "azurerm_synapse_workspace",
        "azurerm_databricks_workspace",
        "azurerm_kusto_cluster",
        "azurerm_data_factory",
        "azurerm_eventgrid_topic",
        "azurerm_servicebus_namespace",
        "azurerm_notification_hub",
    ],
    "gcp": [
        "google_cloud_run_service",
        "google_cloud_run_v2_service",
        "google_vertex_ai_workbench",
        "google_dataproc_cluster",
        "google_dataflow_job",
        "google_bigquery_dataset",
        "google_bigquery_table",
        "google_bigtable_instance",
        "google_spanner_instance",
        "google_pubsub_topic",
        "google_composer_environment",
    ],
}


def fuzzy_match_icon(resource_name: str, available_icons: List[str]) -> List[str]:
    """
    Fuzzy match a Terraform resource name to available icon filenames.
    Returns list of possible matches sorted by relevance.
    """
    # Remove provider prefix
    for prefix in ["aws_", "azurerm_", "google_"]:
        if resource_name.startswith(prefix):
            resource_name = resource_name[len(prefix):]
            break
    
    # Extract keywords from resource name
    keywords = resource_name.replace("_", " ").split()
    
    # Score each icon based on keyword matches
    scores = {}
    for icon in available_icons:
        icon_clean = icon.replace(".png", "").replace("_", " ").lower()
        score = 0
        
        for keyword in keywords:
            if keyword in icon_clean:
                score += 2
            # Partial match
            for word in icon_clean.split():
                if keyword in word or word in keyword:
                    score += 1
        
        if score > 0:
            scores[icon] = score
    
    # Return top matches
    return sorted(scores.keys(), key=lambda k: scores[k], reverse=True)[:5]


def main():
    repo_root = Path(__file__).resolve().parents[1]
    icons_dir = repo_root / "icons"
    
    print("=" * 60)
    print("Icon Mapping Helper")
    print("=" * 60)
    print()
    
    mappings = {}
    
    for provider in ["aws", "azure", "gcp"]:
        provider_dir = icons_dir / provider
        
        if not provider_dir.exists():
            continue
        
        # Get all PNG icons
        icons = [f.name for f in provider_dir.glob("*.png") if f.name != ".gitkeep"]
        
        if not icons:
            print(f"⚠ No icons found in {provider_dir}")
            continue
        
        print(f"\n{provider.upper()} ({len(icons)} icons available)")
        print("-" * 60)
        
        # Map Terraform resources to icons
        tf_key = provider if provider != "azure" else "azure"
        for resource in TERRAFORM_RESOURCES.get(tf_key, []):
            matches = fuzzy_match_icon(resource, icons)
            
            if matches:
                mappings[resource] = {
                    "provider": provider,
                    "suggested_icons": matches[:3],
                    "icon_path": f"icons/{provider}/{matches[0]}"
                }
                print(f"\n  {resource}")
                print(f"    → {matches[0]}")
                if len(matches) > 1:
                    print(f"    Alternatives: {', '.join(matches[1:3])}")
    
    # Save mappings to JSON
    output_file = icons_dir / "icon_mappings.json"
    with open(output_file, "w") as f:
        json.dump(mappings, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✓ Mappings saved to: {output_file}")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review the suggested mappings")
    print("2. Manually rename icons to match Terraform resource types")
    print("3. Remove provider prefix from icon names")
    print("   Example: azurerm_static_web_app → static_web_app.png")
    print()


if __name__ == "__main__":
    main()
