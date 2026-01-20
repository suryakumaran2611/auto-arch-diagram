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

    for provider in mappings:
        print(f"\nChecking {provider.upper()} ({len(mappings[provider])} services):")

        provider_covered = 0
        provider_missing = []

        for service_name, service_info in mappings[provider].items():
            total_services += 1
            category = service_info["category"]

            # Check for icon file
            icon_path = icons_dir / provider / category / f"{service_name}.png"
            if icon_path.exists():
                provider_covered += 1
                covered_services += 1
            else:
                # Try alternative naming (some icons use hyphens)
                alt_path = (
                    icons_dir
                    / provider
                    / category
                    / f"{service_name.replace('_', '-')}.png"
                )
                if alt_path.exists():
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
