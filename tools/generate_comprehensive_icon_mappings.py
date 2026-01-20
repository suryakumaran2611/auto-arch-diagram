#!/usr/bin/env python3
"""
Generate comprehensive icon mappings from service names to actual icon file paths.
This creates a mapping from service names (like 'athena', 'glue', 'lambda') to their
actual PNG file locations in the icons directory.
"""

import json
import os
from pathlib import Path
from typing import Dict, Set


def generate_comprehensive_icon_mappings():
    """Generate mappings from service names to icon file paths."""

    repo_root = Path(__file__).resolve().parents[1]
    icons_dir = repo_root / "icons"

    print("Generating comprehensive icon mappings...")

    # Load service mappings to understand what services we expect
    service_mappings_file = repo_root / "tools" / "comprehensive_service_mappings.json"
    with open(service_mappings_file, "r") as f:
        service_mappings = json.load(f)

    # Scan all PNG files in icons directory
    icon_files = {}
    total_files = 0

    for root, dirs, files in os.walk(icons_dir):
        for file in files:
            if file.endswith(".png"):
                # Get relative path from icons directory
                rel_path = Path(root).relative_to(icons_dir) / file
                icon_files[file.lower()] = str(rel_path)
                total_files += 1

    print(f"   Found {total_files} PNG files in icons directory")

    # Generate mappings for each provider
    comprehensive_mappings = {}

    for provider in service_mappings:
        provider_mappings = {}
        mapped_count = 0

        print(f"\nProcessing {provider.upper()} services...")

        for service_name, service_info in service_mappings[provider].items():
            # Try multiple variations of the service name to find matching icons
            icon_candidates = [
                f"{service_name}.png",
                f"{service_name}-service.png",
                f"{service_name}_service.png",
                f"aws_{service_name}.png",  # AWS-specific
                f"{service_name}s.png",  # Plural forms
                f"{service_name}es.png",  # Plural forms
                f"{service_name}ies.png",  # Plural forms
            ]

            # Add category-specific variations
            category = service_info.get("category", "")
            if category:
                icon_candidates.extend(
                    [
                        f"{category}_{service_name}.png",
                        f"{service_name}_{category}.png",
                    ]
                )

            # Look for matching icon files
            found_path = None
            for candidate in icon_candidates:
                candidate_lower = candidate.lower()
                if candidate_lower in icon_files:
                    found_path = icon_files[candidate_lower]
                    break

            # If not found with direct name, try fuzzy matching
            if not found_path:
                # Try partial matches (e.g., 'lambda' in filename)
                for icon_file, icon_path in icon_files.items():
                    icon_name_no_ext = icon_file[:-4]  # Remove .png
                    if service_name.lower() in icon_name_no_ext.lower():
                        # Check if it's in the right category
                        if category and category in icon_path:
                            found_path = icon_path
                            break
                        elif not found_path:  # Take first match if no category match
                            found_path = icon_path

            if found_path:
                provider_mappings[service_name] = found_path
                mapped_count += 1
                print(f"   [PASS] {service_name} -> {found_path}")
            else:
                # For services without direct icons, use category-based fallback
                fallback_path = f"{provider}/{category}/{service_name}.png"
                provider_mappings[service_name] = fallback_path
                print(f"   [WARN] {service_name} -> {fallback_path} (fallback)")

        comprehensive_mappings[provider] = provider_mappings
        print(
            f"   Results: {mapped_count}/{len(service_mappings[provider])} services mapped"
        )

    # Save the comprehensive mappings
    output_file = icons_dir / "comprehensive_mappings.json"
    with open(output_file, "w") as f:
        json.dump(comprehensive_mappings, f, indent=2)

    # Summary
    total_services = sum(len(mappings) for mappings in service_mappings.values())
    total_mapped = sum(len(mappings) for mappings in comprehensive_mappings.values())

    print("\nComprehensive icon mappings generated!")
    print(f"   Output: {output_file}")
    print(f"   Services: {total_mapped}/{total_services} mapped")
    print(f"   Icon files: {total_files} available")

    # Show sample mappings
    print("\nSample mappings:")
    if "aws" in comprehensive_mappings:
        sample_services = ["lambda", "s3", "ec2", "glue", "athena"]
        for service in sample_services:
            if service in comprehensive_mappings["aws"]:
                print(f"   aws.{service} → {comprehensive_mappings['aws'][service]}")

    return comprehensive_mappings


def validate_mappings():
    """Validate that the generated mappings point to existing files."""

    repo_root = Path(__file__).resolve().parents[1]
    icons_dir = repo_root / "icons"
    mappings_file = icons_dir / "comprehensive_mappings.json"

    if not mappings_file.exists():
        print("❌ Comprehensive mappings file not found")
        return

    with open(mappings_file, "r") as f:
        mappings = json.load(f)

    print("Validating icon mappings...")

    total_mappings = 0
    valid_mappings = 0

    for provider in mappings:
        for service, icon_path in mappings[provider].items():
            total_mappings += 1
            full_path = icons_dir / icon_path

            if full_path.exists():
                valid_mappings += 1
            else:
                print(f"   ❌ Missing: {provider}.{service} → {icon_path}")

    coverage = (valid_mappings / total_mappings * 100) if total_mappings > 0 else 0
    print("\nValidation Results:")
    print(f"   Total mappings: {total_mappings}")
    print(f"   Valid mappings: {valid_mappings}")
    print(f"   Coverage: {coverage:.1f}%")
    if coverage < 100:
        print(
            f"   [WARN] {total_mappings - valid_mappings} mappings point to missing files"
        )

    return coverage >= 80  # Consider good if 80%+ valid


if __name__ == "__main__":
    generate_comprehensive_icon_mappings()
    validate_mappings()
