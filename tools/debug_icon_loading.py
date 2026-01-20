#!/usr/bin/env python3
"""
Debug icon loading for specific Terraform resources from custom-icons-demo
"""

import sys
import json
from pathlib import Path

# Add tools to path
repo_root = Path(__file__).resolve().parents[1]
tools_dir = repo_root / "tools"
sys.path.insert(0, str(tools_dir))


def debug_icon_loading():
    """Debug icon loading for key services from custom-icons-demo."""

    # Load comprehensive mappings
    mappings_file = tools_dir / "comprehensive_service_mappings.json"
    if not mappings_file.exists():
        print("❌ Mappings file not found!")
        return

    with open(mappings_file, "r") as f:
        mappings = json.load(f)

    # Test the key services from custom-icons-demo
    test_resources = [
        "aws_athena_workgroup",  # Should map to athena
        "aws_glue_catalog_database",  # Should map to glue
        "aws_glue_crawler",  # Should map to glue
        "aws_elasticsearch_domain",  # Should map to elasticsearch
        "aws_kinesis_stream",  # Should map to kinesis
        "aws_lambda_function",  # Should map to lambda
        "aws_s3_bucket",  # Should map to s3
        "aws_ec2_instance",  # Should map to ec2
    ]

    print("Debugging icon loading for custom-icons-demo services:")
    print("=" * 60)

    for resource in test_resources:
        print(f"\nResource: {resource}")

        # Extract provider and service name (mimicking the actual code)
        t_clean = resource.lower()
        for prefix in ("aws_", "azurerm_", "google_", "oci_", "ibm_"):
            if t_clean.startswith(prefix):
                t_clean = t_clean[len(prefix) :]
                break

        service_name = t_clean.split("_")[0]  # Get first part before underscore

        print(f"   Cleaned name: {t_clean}")
        print(f"   Service name: {service_name}")

        # Check if service exists in mappings
        provider_normalized = "aws"  # All our test resources are AWS

        if (
            provider_normalized in mappings
            and service_name in mappings[provider_normalized]
        ):
            service_info = mappings[provider_normalized][service_name]
            category = service_info["category"]
            class_name = service_info["class"]
            print(f"   [PASS] Mapped to: {provider_normalized}.{category}.{class_name}")

            # Check if diagrams library has this class
            try:
                import diagrams

                provider_mod = getattr(diagrams, provider_normalized, None)
                if provider_mod:
                    category_mod = getattr(provider_mod, category, None)
                    if category_mod and hasattr(category_mod, class_name):
                        print(
                            f"   [PASS] Diagrams class exists: {provider_normalized}.{category}.{class_name}"
                        )
                    else:
                        print(
                            f"   [FAIL] Diagrams class missing: {provider_normalized}.{category}.{class_name}"
                        )
                else:
                    print(f"   [FAIL] Diagrams provider missing: {provider_normalized}")
            except Exception as e:
                print(f"   [FAIL] Error checking diagrams: {e}")

        else:
            print(f"   [FAIL] Not in mappings: {provider_normalized}.{service_name}")
            # Check what services are available
            if provider_normalized in mappings:
                available = list(mappings[provider_normalized].keys())[:5]
                print(f"   Available services: {', '.join(available)}...")

    print("\n" + "=" * 60)
    print("Summary:")
    print(
        "   - Terraform resources like 'aws_athena_workgroup' should extract 'athena'"
    )
    print("   - 'athena' should map to aws.analytics.Athena in diagrams library")
    print("   - If diagrams class exists, it will be used")
    print("   - Otherwise, falls back to custom icons")


if __name__ == "__main__":
    debug_icon_loading()
