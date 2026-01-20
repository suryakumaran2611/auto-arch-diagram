import time
#!/usr/bin/env python3
"""
Comprehensive icon library manager for auto-arch-diagram.
Downloads and maintains complete icon libraries for all cloud providers.
"""

import os
import json
import requests
import hashlib
from pathlib import Path
from typing import Dict, Set, Optional
from datetime import datetime, timezone



class IconLibraryManager:
    def _github_request_with_retries(self, url, max_retries=5, stream=False):
        """Make a GitHub API request with rate limit and retry handling."""
        attempt = 0
        backoff = 2
        while attempt < max_retries:
            try:
                response = requests.get(url, timeout=30, stream=stream)
                # Check for rate limiting
                if response.status_code == 403 or response.status_code == 429:
                    reset = response.headers.get("X-RateLimit-Reset")
                    remaining = response.headers.get("X-RateLimit-Remaining")
                    if remaining == "0" and reset:
                        reset_time = int(reset)
                        now = int(time.time())
                        wait = max(reset_time - now, 1)
                        print(f"⏳ Rate limit reached. Waiting {wait} seconds until reset...")
                        time.sleep(wait)
                        continue
                    else:
                        print(f"⏳ Rate limit or 403/429 error. Retrying in {backoff} seconds...")
                        time.sleep(backoff)
                        backoff = min(backoff * 2, 60)
                        attempt += 1
                        continue
                if response.status_code in (500, 502, 503, 504):
                    print(f"⚠️ Server error {response.status_code}. Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 60)
                    attempt += 1
                    continue
                return response
            except Exception as e:
                print(f"⚠️ Request error: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                attempt += 1
        print(f"❌ Failed to fetch {url} after {max_retries} attempts.")
        return None

    def download_missing_icons(self):
        """Download only missing or new icons for all providers."""
        print("\n🔍 Downloading only missing or new icons...")
        manifest = self.load_manifest()
        total_downloaded = 0
        for provider in self.providers:
            print(f"\n📦 Processing {provider.upper()}...")
            downloaded = self.download_provider_icons(provider, manifest, force_update=False, only_missing=True)
            total_downloaded += downloaded
            print(f"✅ {provider.upper()}: {downloaded} icons downloaded (missing/new only)")
        self.save_manifest(manifest)
        print(f"\n🎉 Complete! Downloaded {total_downloaded} missing/new icons across {len(self.providers)} providers")
        print(f"📋 Manifest saved to: {self.manifest_file}")

    def download_missing_provider_icons(self, provider: str):
        """Download only missing or new icons for a specific provider."""
        print(f"\n🔍 Downloading only missing or new icons for {provider.upper()}...")
        manifest = self.load_manifest()
        downloaded = self.download_provider_icons(provider, manifest, force_update=False, only_missing=True)
        self.save_manifest(manifest)
        print(f"✅ {provider.upper()}: {downloaded} icons downloaded (missing/new only)")
        print(f"📋 Manifest saved to: {self.manifest_file}")

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.icons_dir = repo_root / "icons"
        self.manifest_file = self.icons_dir / "manifest.json"
        self.github_api_base = (
            "https://api.github.com/repos/mingrammer/diagrams/contents/resources"
        )
        self.providers = ["aws", "azure", "gcp", "oci", "ibm"]

    def download_all_icons(self, force_update: bool = False):
        """Download complete icon libraries for all providers."""
        print("🚀 Starting comprehensive icon library download...")
        print(f"📁 Target directory: {self.icons_dir}")

        # Create icons directory
        self.icons_dir.mkdir(exist_ok=True)

        # Load existing manifest
        manifest = self.load_manifest()

        total_downloaded = 0
        for provider in self.providers:
            print(f"\n📦 Processing {provider.upper()}...")
            downloaded = self.download_provider_icons(provider, manifest, force_update)
            total_downloaded += downloaded
            print(f"✅ {provider.upper()}: {downloaded} icons downloaded")

        # Save updated manifest
        self.save_manifest(manifest)

        print(
            f"\n🎉 Complete! Downloaded {total_downloaded} icons across {len(self.providers)} providers"
        )
        print(f"📋 Manifest saved to: {self.manifest_file}")

    def download_provider_icons(
        self, provider: str, manifest: Dict, force_update: bool = False, only_missing: bool = False
    ) -> int:
        """Download all icons for a specific provider, or only missing/new if only_missing=True."""
        try:
            provider_url = f"{self.github_api_base}/{provider}"
            response = self._github_request_with_retries(provider_url)
            if not response or response.status_code != 200:
                print(f"❌ Failed to list {provider} categories: {response.status_code if response else 'No response'}")
                return 0

            categories = [item for item in response.json() if item["type"] == "dir"]
            provider_dir = self.icons_dir / provider
            provider_dir.mkdir(exist_ok=True)

            downloaded_count = 0
            provider_manifest = manifest.get(provider, {})

            for category in categories:
                category_name = category["name"]
                print(f"  📂 {category_name}")

                category_downloaded = self.download_category_icons(
                    provider,
                    category_name,
                    provider_dir,
                    provider_manifest,
                    force_update,
                    only_missing=only_missing,
                )
                downloaded_count += category_downloaded

                if category_name not in provider_manifest:
                    provider_manifest[category_name] = {}
                provider_manifest[category_name]["downloaded"] = datetime.now(timezone.utc).isoformat()

            return downloaded_count
        except Exception as e:
            print(f"❌ Error downloading {provider} icons: {e}")
            return 0

    def download_category_icons(
        self,
        provider: str,
        category: str,
        provider_dir: Path,
        provider_manifest: Dict,
        force_update: bool = False,
        only_missing: bool = False,
    ) -> int:
        """Download all PNG icons from a specific category, or only missing/new if only_missing=True."""
        try:
            category_url = f"{self.github_api_base}/{provider}/{category}"
            response = self._github_request_with_retries(category_url)
            if not response or response.status_code != 200:
                print(f"    ❌ Failed to list {category}: {response.status_code if response else 'No response'}")
                return 0

            category_dir = provider_dir / category
            category_dir.mkdir(exist_ok=True)

            downloaded_count = 0
            category_manifest = provider_manifest.get(category, {})

            for file_info in response.json():
                if file_info["name"].endswith(".png"):
                    filename = file_info["name"]
                    filepath = category_dir / filename
                    file_hash = self._get_file_hash(file_info)
                    # Only download if missing or hash changed (or forced)
                    if only_missing:
                        should_download = (
                            not filepath.exists() or category_manifest.get(filename) != file_hash
                        )
                    else:
                        should_download = (
                            force_update
                            or not filepath.exists()
                            or category_manifest.get(filename) != file_hash
                        )

                    if should_download:
                        success = self._download_single_icon(file_info, filepath)
                        if success:
                            downloaded_count += 1
                            category_manifest[filename] = file_hash
                        else:
                            print(f"      ❌ Failed to download {filename}")
                    else:
                        if not only_missing:
                            downloaded_count += 1
                        print(f"      ⏭ Skipping {filename} (already exists)")

            return downloaded_count
        except Exception as e:
            print(f"    ❌ Error downloading {category}: {e}")
            return 0

    def _download_single_icon(self, file_info: Dict, filepath: Path) -> bool:
        """Download a single icon file."""
        try:
            download_url = file_info["download_url"]
            response = self._github_request_with_retries(download_url, stream=True)
            if response and response.status_code == 200:
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                print(f"      ❌ HTTP {response.status_code if response else 'No response'} for {file_info['name']}")
                return False
        except Exception as e:
            print(f"      ❌ Error downloading {file_info['name']}: {e}")
            return False

    def _get_file_hash(self, file_info: Dict) -> str:
        """Get a unique hash for a file from GitHub API."""
        # Use SHA as unique identifier
        return file_info.get("sha", "")

    def load_manifest(self) -> Dict:
        """Load the existing manifest file."""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_manifest(self, manifest: Dict):
        """Save the manifest file."""
        with open(self.manifest_file, "w") as f:
            json.dump(manifest, f, indent=2)

    def generate_icon_mappings(self) -> Dict:
        """Generate comprehensive icon mappings based on downloaded files."""
        print("\n🔧 Generating icon mappings...")
        mappings = {}

        for provider in self.providers:
            provider_dir = self.icons_dir / provider
            if not provider_dir.exists():
                continue

            provider_mappings = {}

            # Scan all downloaded files
            for icon_file in provider_dir.rglob("*.png"):
                relative_path = icon_file.relative_to(provider_dir)
                filename = icon_file.name.lower()
                # Remove extension and replace separators
                service_type = filename.replace('.png', '').replace('-', '_').replace(' ', '_')
                # Add mapping for full filename
                provider_mappings[service_type] = str(relative_path)
                # Try to infer service type from filename (legacy logic)
                inferred = self._infer_service_type(filename, provider)
                if inferred and inferred not in provider_mappings:
                    provider_mappings[inferred] = str(relative_path)

            mappings[provider] = provider_mappings
            print(f"  {provider.upper()}: {len(provider_mappings)} mappings generated")

        # Save mappings
        mapping_file = self.icons_dir / "comprehensive_mappings.json"
        with open(mapping_file, "w") as f:
            json.dump(mappings, f, indent=2)

        print(f"💾 Mappings saved to: {mapping_file}")
        return mappings

    def _infer_service_type(self, filename: str, provider: str) -> Optional[str]:
        """Infer service type from icon filename."""
        # Remove .png extension
        name = filename[:-4]

        # Comprehensive keyword mappings
        service_mappings = {
            "aws": {
                "lambda": ["lambda", "lambda-function"],
                "s3": ["s3", "simple-storage-service", "simple-storage"],
                "ec2": ["ec2", "instance", "compute"],
                "rds": ["rds", "database", "sql"],
                "dynamodb": ["dynamodb", "nosql"],
                "vpc": ["vpc", "network", "virtual"],
                "iam": ["iam", "identity", "role"],
                "kms": ["kms", "key", "encryption"],
                "cloudwatch": ["cloudwatch", "monitor", "logs"],
                "sns": ["sns", "notification", "topic"],
                "sqs": ["sqs", "queue", "message"],
                "apigateway": ["api-gateway", "api", "gateway", "rest"],
                "cloudfront": ["cloudfront", "cdn", "distribution"],
                "ebs": ["ebs", "elastic-block", "volume"],
                "efs": ["efs", "elastic-file", "filesystem"],
                "eks": ["eks", "kubernetes", "container"],
                "ecs": ["ecs", "container", "service"],
                "batch": ["batch", "job"],
                "aurora": ["aurora", "mysql"],
                "neptune": ["neptune", "graph"],
                "redshift": ["redshift", "warehouse"],
                "kinesis": ["kinesis", "stream"],
                "eventbridge": ["eventbridge", "event", "bus"],
                "secretsmanager": ["secrets", "secret", "manager"],
                "cloudtrail": ["cloudtrail", "audit", "log"],
                "guardduty": ["guardduty", "security", "threat"],
                "waf": ["waf", "firewall", "web"],
                "xray": ["x-ray", "xray", "tracing"],
            },
            "azure": {
                "virtual_machine": ["vm", "virtual", "machine", "compute"],
                "storage_account": ["storage", "account", "blob"],
                "function_app": ["function", "app", "serverless"],
                "key_vault": ["vault", "key", "secret"],
                "sql_database": ["sql", "database", "azure"],
                "load_balancer": ["load", "balancer", "lb"],
                "application_gateway": ["app-gateway", "gateway", "waf"],
                "aks": ["kubernetes", "aks", "container"],
                "app_service": ["app", "service", "web"],
                "cosmos_db": ["cosmos", "nosql", "document"],
                "event_grid": ["event", "grid", "pubsub"],
                "service_bus": ["service", "bus", "queue"],
                "monitor": ["monitor", "insights"],
            },
            "gcp": {
                "compute_engine": ["compute", "engine", "gce"],
                "cloud_storage": ["storage", "gcs", "bucket"],
                "cloud_sql": ["sql", "database", "cloud"],
                "bigquery": ["bigquery", "data", "warehouse"],
                "cloud_functions": ["function", "serverless", "cloud"],
                "gke": ["gke", "kubernetes", "container"],
                "cloud_run": ["run", "serverless", "app"],
                "spanner": ["spanner", "database", "global"],
                "bigtable": ["bigtable", "nosql", "scalable"],
                "pubsub": ["pubsub", "topic", "message"],
                "iam": ["iam", "identity", "policy"],
                "kms": ["kms", "key", "encryption"],
            },
        }

        if provider in service_mappings:
            for service_type, keywords in service_mappings[provider].items():
                if any(keyword in name for keyword in keywords):
                    return service_type

        # Fallback: try to extract from filename patterns
        if "-" in name:
            parts = name.split("-")
            if len(parts) > 1 and parts[0] in ["ec2", "s3", "iam", "vpc", "eks"]:
                return parts[0]

        return None

    def cleanup_orphaned_icons(self):
        """Remove icons that are no longer available upstream."""
        print("\n🧹 Cleaning up orphaned icons...")
        # This would compare local files with upstream and remove obsolete ones
        pass

    def update_icons(self, check_updates: bool = True):
        """Update existing icons (check for changes, download new ones)."""
        print("🔄 Checking for icon updates...")
        self.download_all_icons(force_update=True)
        self.generate_icon_mappings()
        print("✅ Icon library update complete!")


def main():
    """Main entry point for icon library management."""
    import sys

    if len(sys.argv) < 2:
        print("📖 Icon Library Manager for Auto-Arch-Diagram")
        print("\nUsage: python icon_library.py <command> [options]")
        print("\nCommands:")
        print("  download-all [--force]     Download complete icon libraries")
        print("  download <provider>        Download icons for specific provider")
        print("  update                   Update existing icons")
        print("  mappings                 Generate icon mappings")
        print("  stats                    Show library statistics")
        print("\nOptions:")
        print("  --force                 Force re-download all files")
        print("\nProviders:", ", ".join(["aws", "azure", "gcp", "oci", "ibm"]))
        sys.exit(1)

    # Get repo root
    repo_root = Path(__file__).resolve().parents[1]
    manager = IconLibraryManager(repo_root)

    # Add download-missing command
    # Usage: python icon_library.py download-missing [<provider>]

    command = sys.argv[1]
    force_flag = "--force" in sys.argv


    if command == "download-all":
        manager.download_all_icons(force_update=force_flag)
        manager.generate_icon_mappings()

    elif command == "download-missing":
        if len(sys.argv) == 2:
            manager.download_missing_icons()
            manager.generate_icon_mappings()
        elif len(sys.argv) == 3:
            provider = sys.argv[2]
            if provider not in manager.providers:
                print(f"❌ Unknown provider: {provider}")
                sys.exit(1)
            manager.download_missing_provider_icons(provider)
            manager.generate_icon_mappings()
        else:
            print("❌ Usage: python icon_library.py download-missing [<provider>]")
            sys.exit(1)

    elif command == "download":
        if len(sys.argv) < 3:
            print("❌ Please specify a provider")
            sys.exit(1)
        provider = sys.argv[2]
        if provider not in manager.providers:
            print(f"❌ Unknown provider: {provider}")
            sys.exit(1)

        manager.download_provider_icons(
            provider, manager.load_manifest(), force_update=force_flag
        )
        manager.generate_icon_mappings()

    elif command == "update":
        manager.update_icons()

    elif command == "mappings":
        manager.generate_icon_mappings()

    elif command == "stats":
        manager.show_statistics()

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
