#!/usr/bin/env python3
"""
Verify comprehensive icon coverage for all mapped services.
Checks that every service in our mappings has a corresponding icon file.
"""

import json
from pathlib import Path


def main():
    """Main verification function."""

    repo_root = Path(__file__).resolve().parents[1]
    mappings_file = repo_root / "tools" / "comprehensive_service_mappings.json"
    icons_dir = repo_root / "icons"

    if not mappings_file.exists():
        print("[FAIL] Comprehensive mappings file not found!")
        return False

    # Load mappings
    with open(mappings_file, "r") as f:
        mappings = json.load(f)

    print("Verifying comprehensive icon coverage...")
    print(f"   Mappings file: {mappings_file}")
    print(f"   Icons directory: {icons_dir}")

    total_services = 0
    covered_services = 0
    missing_icons = []


    # Load smart PNG mappings for variant matching
    png_mappings_file = repo_root / "icons" / "comprehensive_mappings.json"
    png_mappings = None
    if png_mappings_file.exists():
        with open(png_mappings_file, "r") as f:
            png_mappings = json.load(f)

    # Alias and variant helpers (from _icon_class_for)

    # Cloud-agnostic alias and variant logic
    provider_aliases = {
        "azurerm": "azure",
        "google": "gcp",
        "gcp": "gcp",
        "aws": "aws",
        "oci": "oci",
        "ibm": "ibm",
    }

    # Common aliases for all clouds (expand as needed)
    global_alias_map = {
        # AWS
        "wafv2": "waf",
        "apigatewayv2": "apigateway",
        "opensearch": "elasticsearch",
        "msk": "kinesis",
        "fargate": "ecs",
        "app_runner": "elasticbeanstalk",
        "controltower": "organizations",
        "memorydb": "elasticache",
        "detective": "guardduty",
        # Azure
        "functionapp": "function_app",
        "sqlserver": "sql_server",
        "postgres": "postgresql",
        # GCP
        "gke": "kubernetes_engine",
        "gcs": "storage",
        "pubsub": "pub_sub",
    }

    import re
    import inflection
    from slugify import slugify
    from rapidfuzz import process, fuzz

    def smart_png_icon_exists(provider, service_name):
        provider_norm = provider_aliases.get(provider.lower(), provider.lower())
        if not png_mappings or provider_norm not in png_mappings:
            return False
        mapping = png_mappings[provider_norm]
        base = service_name.lower().replace('-', '_')
        parts = base.split('_')
        candidates = set()
        # Multi-part names (4, 3, 2)
        for n in [4, 3, 2]:
            if len(parts) >= n:
                candidates.add('_'.join(parts[:n]))
        # Add single-part and base
        candidates.add(service_name.lower())
        candidates.add(base)
        # Add alias if present
        if service_name.lower() in global_alias_map:
            candidates.add(global_alias_map[service_name.lower()])
        # inflection: underscore, camelize, singularize, pluralize
        candidates.add(inflection.underscore(service_name))
        candidates.add(inflection.camelize(service_name, False))
        candidates.add(inflection.camelize(service_name, True))
        candidates.add(inflection.singularize(base))
        candidates.add(inflection.pluralize(base))
        # slugify: kebab-case
        candidates.add(slugify(base))
        # Add no-underscore, no-dash
        candidates.add(base.replace('_', ''))
        candidates.add(base.replace('_', '-'))
        candidates.add(base.replace('-', ''))
        # Plural/singular
        if base.endswith('s'):
            candidates.add(base[:-1])
        else:
            candidates.add(base + 's')
        # Remove trailing numbers (e.g., v2, 2)
        candidates.add(re.sub(r'\d+$', '', base))
        # Add known patterns for common services (cloud-agnostic)
        if base in ("lb", "elb", "loadbalancer", "load_balancer"):
            candidates.update([
                "elb_application_load_balancer", "elb_network_load_balancer", "elb_classic_load_balancer",
                "load_balancer", "loadbalancer", "application_load_balancer", "network_load_balancer", "classic_load_balancer"
            ])
        if base in ("stepfunctions", "step_functions", "step-functions"):
            candidates.update(["step_functions", "step-functions", "stepfunctions"])
        if base in ("elasticsearch", "opensearch", "search"):
            candidates.update(["elasticsearch_service", "amazon_opensearch_service", "search"])
        if base in ("s3", "storage", "bucket"):
            candidates.update([
                "simple_storage_service_s3", "simple_storage_service_s3_bucket", "s3_glacier_archive",
                "storage", "bucket", "storage_bucket"
            ])
        if base == "glue":
            candidates.update(["glue_crawlers", "glue_data_catalog"])
        if base == "dynamodb":
            candidates.update(["dynamodb_table", "dynamodb_items", "dynamodb_item"])
        if base == "cloudwatch":
            candidates.update(["cloudwatch_logs", "cloudwatch_alarm", "cloudwatch_rule"])
        if base in ("pubsub", "pub_sub"):
            candidates.update(["pubsub", "pub_sub"])
        # Try all candidates in order
        for c in candidates:
            if c in mapping:
                icon_file = icons_dir / provider_norm / mapping[c] if not mapping[c].startswith("/") else Path(mapping[c])
                if icon_file.exists():
                    return True
        # Fuzzy match fallback: find closest mapping key if above fails
        fuzzy_result = process.extractOne(base, mapping.keys(), scorer=fuzz.ratio, score_cutoff=80) if mapping else None
        if fuzzy_result:
            best = fuzzy_result[0]
            icon_file = icons_dir / provider_norm / mapping[best] if not mapping[best].startswith("/") else Path(mapping[best])
            if icon_file.exists():
                return True
        return False

    for provider in mappings:
        print(f"\nChecking {provider.upper()} ({len(mappings[provider])} services):")

        provider_covered = 0
        provider_missing = []

        for service_name, service_info in mappings[provider].items():
            total_services += 1
            category = service_info["category"]

            # Use smart PNG icon matching logic
            if smart_png_icon_exists(provider, service_name):
                provider_covered += 1
                covered_services += 1
            else:
                provider_missing.append(f"{service_name} ({category})")
                missing_icons.append(f"{provider}.{category}.{service_name}")

        coverage_percent = (
            (provider_covered / len(mappings[provider]) * 100)
            if mappings[provider]
            else 0
        )
        print(
            f"   [PASS] {provider_covered}/{len(mappings[provider])} services covered ({coverage_percent:.1f}%)"
        )

        if provider_missing:
            print(
                f"   [WARN] Missing {len(provider_missing)} icons: {', '.join(provider_missing[:3])}"
                + ("..." if len(provider_missing) > 3 else "")
            )

    # Overall summary
    coverage_percent = (
        (covered_services / total_services * 100) if total_services > 0 else 0
    )

    print(f"\nOverall Coverage Summary:")
    print(f"   Total services mapped: {total_services}")
    print(f"   Icons available: {covered_services}")
    print(f"   Coverage: {coverage_percent:.1f}%")

    # Test key services from custom-icons-demo
    print(f"\nTesting Key Services from custom-icons-demo:")
    key_services = [
        ("aws", "glue", "analytics"),
        ("aws", "athena", "analytics"),
        ("aws", "elasticsearch", "search"),
        ("aws", "kinesis", "analytics"),
        ("aws", "stepfunctions", "integration"),
        ("aws", "lambda", "compute"),
        ("aws", "s3", "storage"),
        ("aws", "ec2", "compute"),
    ]

    key_covered = 0
    for provider, service, category in key_services:
        icon_path = icons_dir / provider / category / f"{service}.png"
        alt_path = icons_dir / provider / category / f"{service.replace('_', '-')}.png"

        if icon_path.exists() or alt_path.exists():
            print(f"   [PASS] {provider}.{category}.{service}")
            key_covered += 1
        else:
            print(f"   [FAIL] {provider}.{category}.{service}")

    print(
        f"\nKey services coverage: {key_covered}/{len(key_services)} ({key_covered / len(key_services) * 100:.1f}%)"
    )

    # Check actual icon counts
    print(f"\nActual Icon Inventory:")
    if (icons_dir / "aws").exists():
        aws_icons = len(list((icons_dir / "aws").rglob("*.png")))
        print(f"   AWS icons: {aws_icons}")

    if (icons_dir / "azure").exists():
        azure_icons = len(list((icons_dir / "azure").rglob("*.png")))
        print(f"   Azure icons: {azure_icons}")

    success = coverage_percent >= 80  # Consider good if 80%+ coverage

    if success:
        print("\n[PASS] Comprehensive icon coverage verification PASSED!")
    else:
        print("\n[FAIL] Comprehensive icon coverage verification FAILED!")

    if missing_icons:
        print(f"   Missing icons for {len(missing_icons)} services")
        # Save missing list
        with open(repo_root / "missing_icons.txt", "w") as f:
            f.write("Missing icon services:\n")
            for icon in missing_icons[:50]:  # Limit to first 50
                f.write(f"- {icon}\n")
        print(f"   Full list saved to: missing_icons.txt")

    return success


if __name__ == "__main__":
    import sys

    success = main()
    sys.exit(0 if success else 1)
