#!/usr/bin/env python3
"""
Optimized icon loading solution for auto-arch-diagram.
Prioritizes the diagrams library over custom icons.
"""

import os
import sys
from pathlib import Path


def setup_optimized_icon_loading():
    """Setup optimized icon loading that uses diagrams library as primary source."""

    # Get repo root
    repo_root = Path(__file__).resolve().parents[0]
    icons_dir = repo_root / "icons"

    print("🔧 Setting up optimized icon loading...")
    print(f"📁 Icons directory: {icons_dir}")

    # Check what we have available
    aws_icons = {}
    if (icons_dir / "aws").exists():
        aws_icons["compute"] = len(list((icons_dir / "aws/compute").glob("*.png")))
        aws_icons["storage"] = len(list((icons_dir / "aws/storage").glob("*.png")))
        aws_icons["network"] = len(list((icons_dir / "aws/network").glob("*.png")))
        aws_icons["security"] = len(list((icons_dir / "aws/security").glob("*.png")))
        aws_icons["database"] = len(list((icons_dir / "aws/database").glob("*.png")))
        aws_icons["integration"] = len(
            list((icons_dir / "aws/integration").glob("*.png"))
        )
        aws_icons["management"] = len(
            list((icons_dir / "aws/management").glob("*.png"))
        )

        print(f"   AWS icons by category:")
        for category, count in aws_icons.items():
            if count > 0:
                print(f"      {category}: {count} icons")

        total_aws = sum(aws_icons.values())
        print(f"   Total AWS icons: {total_aws}")

    # Set environment variables for optimal loading
    os.environ["AUTO_ARCH_PREFER_DIAGRAMS"] = "true"
    os.environ["AUTO_ARCH_DEBUG"] = "false"  # Reduce debug noise
    os.environ["AUTO_ARCH_DOWNLOAD_ICONS"] = "false"  # Don't download by default

    print("✅ Optimized icon loading configured!")
    print("   - Will prioritize diagrams library icons")
    print("   - Disabled debug output for cleaner generation")
    print("   - Disabled automatic downloading (use scripts manually if needed)")


def verify_diagrams_library():
    """Verify that diagrams library has the icons we need."""
    try:
        import diagrams

        print("\n🔍 Verifying diagrams library...")

        # Check key services
        key_services = ["Lambda", "S3", "EC2", "RDS", "IAM", "VPC"]
        found_services = []

        if hasattr(diagrams, "aws"):
            # Check AWS module
            if hasattr(diagrams.aws, "compute"):
                if hasattr(diagrams.aws.compute, "Lambda"):
                    found_services.append("Lambda")
                if hasattr(diagrams.aws.compute, "EC2"):
                    found_services.append("EC2")

            if hasattr(diagrams.aws, "storage"):
                if hasattr(diagrams.aws.storage, "SimpleStorageServiceS3"):
                    found_services.append("S3")

            if hasattr(diagrams.aws, "network"):
                if hasattr(diagrams.aws.network, "VPC"):
                    found_services.append("VPC")

            if hasattr(diagrams.aws, "security"):
                if hasattr(diagrams.aws.security, "IAM"):
                    found_services.append("IAM")

            if hasattr(diagrams.aws, "database"):
                if hasattr(diagrams.aws.database, "RDS"):
                    found_services.append("RDS")

        print(f"   ✅ Diagrams library has: {', '.join(found_services)}")

        missing = [s for s in key_services if s not in found_services]
        if missing:
            print(f"   ❌ Missing from diagrams: {', '.join(missing)}")
            return False
        else:
            print("   ✅ All key services available in diagrams library!")
            return True

    except ImportError:
        print("   ❌ Diagrams library not installed")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        success = verify_diagrams_library()
        sys.exit(0 if success else 1)
    else:
        setup_optimized_icon_loading()
        print("\nUsage:")
        print("  python optimize_icon_loading.py --verify")
        print("  python optimize_icon_loading.py")
