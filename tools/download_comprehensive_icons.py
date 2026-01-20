#!/usr/bin/env python3
"""
Download comprehensive icons for ALL mapped services across AWS, Azure, and GCP.
This ensures every service in our mappings has a corresponding icon file.
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Set


def download_comprehensive_icons():
    """Download icons for all services in our comprehensive mappings."""

    repo_root = Path(__file__).resolve().parents[1]
    mappings_file = repo_root / "tools" / "comprehensive_service_mappings.json"
    icons_dir = repo_root / "icons"

    if not mappings_file.exists():
        print("ERROR: Comprehensive mappings file not found!")
        print("Run: python tools/comprehensive_service_mappings.py")
        return

    # Load mappings
    with open(mappings_file, "r") as f:
        mappings = json.load(f)

    print("Starting comprehensive icon download...")

    total_downloaded = 0
    total_skipped = 0

    for provider in mappings:
        print(f"\nProcessing {provider.upper()}...")

        provider_downloaded = 0
        provider_skipped = 0

        for service_name, service_info in mappings[provider].items():
            category = service_info["category"]

            # Create category directory
            category_dir = icons_dir / provider / category
            category_dir.mkdir(parents=True, exist_ok=True)

            # Check if icon already exists
            icon_path = category_dir / f"{service_name}.png"
            if icon_path.exists():
                provider_skipped += 1
                total_skipped += 1
                continue

            # Try to download the icon
            success = download_service_icon(provider, category, service_name, icon_path)
            if success:
                provider_downloaded += 1
                total_downloaded += 1
                print(f"   OK: {provider}.{category}.{service_name}")
            else:
                print(f"   FAILED: {provider}.{category}.{service_name} (failed)")

        print(
            f"   {provider}: {provider_downloaded} downloaded, {provider_skipped} skipped"
        )

    print("\nComprehensive icon download complete!")
    print(f"   Downloaded: {total_downloaded}")
    print(f"   Skipped: {total_skipped}")
    print(f"   Icons directory: {icons_dir}")

    # Update manifest
    update_manifest(icons_dir, mappings)


def download_service_icon(
    provider: str, category: str, service_name: str, icon_path: Path
) -> bool:
    """Download a single service icon from GitHub."""
    try:
        # Try multiple possible icon names/patterns
        possible_names = [
            f"{service_name}.png",
            f"{service_name.replace('_', '-')}.png",
            f"{service_name.replace('_', '')}.png",
            f"{provider}_{service_name}.png",
            f"{provider}_{service_name.replace('_', '-')}.png",
        ]

        # Try different categories too (some services might be in different categories in diagrams repo)
        categories_to_try = [category]
        if category == "analytics":
            categories_to_try.extend(["business", "database", "integration"])
        elif category == "ml":
            categories_to_try.extend(["ai", "analytics"])
        elif category == "search":
            categories_to_try.extend(["database", "analytics"])

        for cat in categories_to_try:
            for name in possible_names:
                download_url = f"https://raw.githubusercontent.com/mingrammer/diagrams/master/resources/{provider}/{cat}/{name}"
                response = requests.get(download_url, timeout=5)

                if response.status_code == 200:
                    with open(icon_path, "wb") as f:
                        f.write(response.content)
                    return True

        return False

    except Exception:
        return False


def update_manifest(icons_dir: Path, mappings: Dict):
    """Update the manifest with download information."""
    manifest_file = icons_dir / "comprehensive_manifest.json"

    manifest = {
        "last_updated": str(Path(__file__).stat().st_mtime),
        "providers": {},
        "total_icons": 0,
        "categories": {},
    }

    total_icons = 0
    categories = {}

    for provider in mappings:
        provider_dir = icons_dir / provider
        provider_count = 0

        if provider_dir.exists():
            for category_dir in provider_dir.iterdir():
                if category_dir.is_dir():
                    category_name = category_dir.name
                    icon_count = len(list(category_dir.glob("*.png")))

                    if category_name not in categories:
                        categories[category_name] = 0
                    categories[category_name] += icon_count

                    provider_count += icon_count

        manifest["providers"][provider] = {
            "services_mapped": len(mappings[provider]),
            "icons_downloaded": provider_count,
        }
        total_icons += provider_count

    manifest["total_icons"] = total_icons
    manifest["categories"] = categories

    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest updated: {manifest_file}")


def verify_comprehensive_coverage():
    """Verify that we have icons for all mapped services."""
    repo_root = Path(__file__).resolve().parents[1]
    mappings_file = repo_root / "tools" / "comprehensive_service_mappings.json"
    icons_dir = repo_root / "icons"

    if not mappings_file.exists():
        print("ERROR: Mappings file not found")
        return

    with open(mappings_file, "r") as f:
        mappings = json.load(f)

    print("Verifying comprehensive icon coverage...")

    total_services = 0
    covered_services = 0

    for provider in mappings:
        print(f"\n{provider.upper()}:")

        for service_name, service_info in mappings[provider].items():
            total_services += 1
            category = service_info["category"]
            icon_path = icons_dir / provider / category / f"{service_name}.png"

            if icon_path.exists():
                covered_services += 1
            else:
                print(f"   WARNING: Missing: {provider}.{category}.{service_name}")

    coverage_percent = (
        (covered_services / total_services * 100) if total_services > 0 else 0
    )

    print("\nCoverage Summary:")
    print(f"   Total services mapped: {total_services}")
    print(f"   Icons available: {covered_services}")
    print(f"   Coverage: {coverage_percent:.1f}%")
    if coverage_percent < 100:
        print(f"   WARNING: {total_services - covered_services} services missing icons")
    else:
        print("   SUCCESS: All services have icons!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_comprehensive_coverage()
    else:
        download_comprehensive_icons()
        verify_comprehensive_coverage()
