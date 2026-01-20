#!/usr/bin/env python3
"""
Dynamic icon fetching utility for cloud provider icons.
Downloads missing icons from the diagrams repository when needed.
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional


def download_latest_icons(provider="aws", category="all", limit=None):
    """
    Downloads latest icons from diagrams repository.

    Args:
        provider: Cloud provider (aws, azure, gcp, etc.)
        category: Service category (ml, storage, compute, etc.) or "all"
        limit: Maximum number of icons to download (None for unlimited)
    """
    repo_root = Path(__file__).resolve().parents[1]
    icons_dir = repo_root / "icons" / provider
    icons_dir.mkdir(parents=True, exist_ok=True)

    # GitHub API base URL
    base_url = "https://api.github.com/repos/mingrammer/diagrams/contents/resources"

    try:
        if category == "all":
            # Get all categories for this provider
            provider_url = f"{base_url}/{provider}"
            response = requests.get(provider_url, timeout=30)
            if response.status_code != 200:
                print(f"Provider folder not found: {provider}")
                return

            folders = [item for item in response.json() if item["type"] == "dir"]
            downloaded = 0

            for folder in folders[:limit] if limit else folders:
                if download_category_icons(
                    base_url, provider, folder["name"], icons_dir
                ):
                    downloaded += 1
                if limit and downloaded >= limit:
                    break

            print(f"Downloaded {downloaded} categories for {provider}")
        else:
            # Download specific category
            success = download_category_icons(base_url, provider, category, icons_dir)
            if success:
                print(f"Downloaded {category} icons for {provider}")
            else:
                print(f"Failed to download {category} icons for {provider}")

    except Exception as e:
        print(f"Error downloading icons: {e}")


def download_category_icons(
    base_url: str, provider: str, category: str, icons_dir: Path
) -> bool:
    """Download all PNG icons from a specific category."""
    try:
        category_url = f"{base_url}/{provider}/{category}"
        response = requests.get(category_url, timeout=30)
        if response.status_code != 200:
            print(f"Category folder not found: {provider}/{category}")
            return False

        category_dir = icons_dir / category
        category_dir.mkdir(exist_ok=True)

        downloaded_count = 0
        for file_info in response.json():
            if file_info["name"].endswith(".png"):
                download_icon(file_info, category_dir)
                downloaded_count += 1

        print(f"  Downloaded {downloaded_count} icons from {provider}/{category}")
        return downloaded_count > 0

    except Exception as e:
        print(f"Error downloading {provider}/{category}: {e}")
        return False


def download_icon(file_info: dict, target_dir: Path):
    """Download a single icon file."""
    try:
        download_url = file_info["download_url"]
        filename = file_info["name"]
        filepath = target_dir / filename

        # Skip if already exists
        if filepath.exists():
            print(f"  Skipping {filename} (already exists)")
            return

        response = requests.get(download_url, timeout=30)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"  Downloaded {filename}")
        else:
            print(f"  Failed to download {filename}: {response.status_code}")

    except Exception as e:
        print(f"  Error downloading {file_info['name']}: {e}")


def get_available_categories(provider: str) -> list[str]:
    """Get available categories for a provider."""
    try:
        url = f"https://api.github.com/repos/mingrammer/diagrams/contents/resources/{provider}"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return []

        return [item["name"] for item in response.json() if item["type"] == "dir"]
    except Exception:
        return []


def search_icons(provider: str, service_name: str) -> Optional[str]:
    """Search for a specific service icon across all categories."""
    categories = get_available_categories(provider)

    for category in categories:
        try:
            url = f"https://api.github.com/repos/mingrammer/diagrams/contents/resources/{provider}/{category}"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue

            for file_info in response.json():
                if file_info["name"].endswith(".png"):
                    if service_name.lower() in file_info["name"].lower():
                        return file_info["download_url"]
        except Exception:
            continue

    return None


def update_icon_mappings():
    """Update icon mappings based on available icons."""
    repo_root = Path(__file__).resolve().parents[1]
    mapping_file = repo_root / "icons" / "icon_mappings.json"

    providers = ["aws", "azure", "gcp"]
    all_mappings = {}

    for provider in providers:
        categories = get_available_categories(provider)
        provider_mappings = {}

        for category in categories:
            try:
                url = f"https://api.github.com/repos/mingrammer/diagrams/contents/resources/{provider}/{category}"
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    continue

                for file_info in response.json():
                    if file_info["name"].endswith(".png"):
                        # Create a mapping from filename to service type
                        icon_name = file_info["name"].replace(".png", "")
                        service_type = infer_service_type(icon_name, provider)
                        if service_type:
                            provider_mappings[service_type] = icon_name

            except Exception:
                continue

        all_mappings[provider] = provider_mappings
        print(f"Generated {len(provider_mappings)} mappings for {provider}")

    # Save mappings
    with open(mapping_file, "w") as f:
        json.dump(all_mappings, f, indent=2)

    print(f"Icon mappings saved to {mapping_file}")


def infer_service_type(icon_name: str, provider: str) -> Optional[str]:
    """Infer service type from icon filename."""
    # Service keyword mapping
    service_keywords = {
        "aws": {
            "lambda": ["lambda", "function"],
            "s3": ["s3", "storage", "simple"],
            "ec2": ["ec2", "instance", "compute"],
            "rds": ["rds", "database", "sql"],
            "dynamodb": ["dynamodb", "nosql"],
            "vpc": ["vpc", "network", "virtual"],
            "iam": ["iam", "identity", "role"],
            "kms": ["kms", "key", "encryption"],
            "cloudwatch": ["cloudwatch", "monitor", "logs"],
            "sns": ["sns", "notification", "topic"],
            "sqs": ["sqs", "queue", "message"],
            "apigateway": ["api", "gateway", "rest"],
        },
        "azure": {
            "virtual_machine": ["vm", "virtual", "machine"],
            "storage_account": ["storage", "account", "blob"],
            "function_app": ["function", "app", "serverless"],
            "key_vault": ["vault", "key", "secret"],
            "sql_database": ["sql", "database", "azure"],
            "load_balancer": ["load", "balancer", "lb"],
        },
        "gcp": {
            "compute_engine": ["compute", "engine", "gce"],
            "cloud_storage": ["storage", "gcs", "bucket"],
            "cloud_sql": ["sql", "database", "cloud"],
            "bigquery": ["bigquery", "data", "warehouse"],
            "cloud_functions": ["function", "serverless", "cloud"],
            "gke": ["gke", "kubernetes", "container"],
            "cloud_run": ["run", "serverless", "app"],
        },
    }

    if provider in service_keywords:
        for service_type, keywords in service_keywords[provider].items():
            if any(keyword in icon_name.lower() for keyword in keywords):
                return service_type

    return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python icon_fetcher.py <command> [args]")
        print("Commands:")
        print(
            "  download <provider> [category]  - Download icons for provider/category"
        )
        print("  update-mappings              - Update icon mappings")
        print("  search <provider> <service>  - Search for specific icon")
        print("  categories <provider>         - List available categories")
        sys.exit(1)

    command = sys.argv[1]

    if command == "download":
        provider = sys.argv[2] if len(sys.argv) > 2 else "aws"
        category = sys.argv[3] if len(sys.argv) > 3 else "all"
        limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
        download_latest_icons(provider, category, limit)

    elif command == "update-mappings":
        update_icon_mappings()

    elif command == "search":
        provider = sys.argv[2] if len(sys.argv) > 2 else "aws"
        service = sys.argv[3] if len(sys.argv) > 3 else "lambda"
        icon_url = search_icons(provider, service)
        if icon_url:
            print(f"Found icon: {icon_url}")
        else:
            print(f"Icon not found for {provider}.{service}")

    elif command == "categories":
        provider = sys.argv[2] if len(sys.argv) > 2 else "aws"
        categories = get_available_categories(provider)
        print(f"Available categories for {provider}:")
        for cat in categories:
            print(f"  {cat}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
