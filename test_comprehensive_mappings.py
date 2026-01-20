#!/usr/bin/env python3
"""
Test comprehensive service mappings for Glue, Athena, Elasticsearch, etc.
"""

import sys
import json
from pathlib import Path

# Add tools to path
repo_root = Path(__file__).resolve().parents[0]
tools_dir = repo_root / "tools"
sys.path.insert(0, str(tools_dir))


def test_comprehensive_mappings():
    """Test that services like Glue, Athena, Elasticsearch now have proper mappings."""
    print("Testing comprehensive service mappings...")

    # Load the comprehensive mappings
    mappings_file = tools_dir / "comprehensive_service_mappings.json"
    if not mappings_file.exists():
        print("❌ Comprehensive mappings file not found!")
        return

    with open(mappings_file, "r") as f:
        mappings = json.load(f)

    # Test key services that were previously missing
    test_services = [
        ("aws", "glue", "AWS Glue"),
        ("aws", "athena", "Amazon Athena"),
        ("aws", "elasticsearch", "OpenSearch Service"),
        ("aws", "kinesis", "Kinesis"),
        ("aws", "stepfunctions", "Step Functions"),
        ("aws", "sagemaker", "SageMaker"),
        ("aws", "comprehend", "Comprehend"),
        ("aws", "rekognition", "Rekognition"),
        ("aws", "bedrock", "Bedrock"),
        ("aws", "groundstation", "Ground Station"),
        ("aws", "braket", "Braket"),
    ]

    print("\nChecking service mappings:")
    found_count = 0

    for provider, service, description in test_services:
        if provider in mappings and service in mappings[provider]:
            service_info = mappings[provider][service]
            category = service_info["category"]
            class_name = service_info["class"]
            print(f"   [PASS] {description}: {provider}.{category}.{class_name}")
            found_count += 1
        else:
            print(f"   [FAIL] {description}: Not found")

    print(f"\nResults: {found_count}/{len(test_services)} services properly mapped")

    # Test diagrams library availability
    print("\nTesting diagrams library availability:")
    try:
        import diagrams

        print("   [PASS] Diagrams library imported successfully")

        # Check if key AWS modules exist
        try:
            from diagrams.aws import compute, storage, database

            print("   [PASS] AWS modules available (compute, storage, database)")
        except ImportError:
            print("   [WARN] Some AWS modules not available")

    except ImportError:
        print("   [FAIL] Diagrams library not available")
    except Exception as e:
        print(f"   [FAIL] Error testing diagrams library: {e}")

    print("\nComprehensive mapping test completed!")


if __name__ == "__main__":
    test_comprehensive_mappings()
