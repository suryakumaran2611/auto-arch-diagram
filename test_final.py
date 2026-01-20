#!/usr/bin/env python3
"""Simple test for icon loading fixes"""

import sys
from pathlib import Path

# Add tools to path
repo_root = Path(__file__).resolve().parents[0]
tools_dir = repo_root / "tools"
sys.path.insert(0, str(tools_dir))

try:
    from generate_arch_diagram import _load_custom_icon, _icon_class_for

    print("Testing icon loading fixes...")

    # Test with lambda - should now work since we downloaded it
    print("\n1. Testing AWS Lambda...")
    lambda_icon = _load_custom_icon("aws_lambda")
    if lambda_icon:
        print("   [PASS] AWS Lambda icon loaded successfully")
    else:
        print("   [FAIL] AWS Lambda icon not found")

    # Test with S3
    print("\n2. Testing AWS S3...")
    s3_icon = _load_custom_icon("aws_s3")
    if s3_icon:
        print("   [PASS] AWS S3 icon loaded successfully")
    else:
        print("   [FAIL] AWS S3 icon not found")

    # Test icon class resolution (this uses diagrams library)
    print("\n3. Testing diagrams library icon class resolution...")
    lambda_class = _icon_class_for("aws_lambda")
    s3_class = _icon_class_for("aws_s3")
    ec2_class = _icon_class_for("aws_ec2")

    print(f"   AWS Lambda class: {lambda_class}")
    print(f"   AWS S3 class: {s3_class}")
    print(f"   AWS EC2 class: {ec2_class}")

    # Check if icons directory has the expected files
    icons_dir = repo_root / "icons" / "aws"

    print("\n4. Checking available AWS icons...")
    if icons_dir.exists():
        compute_icons = list((icons_dir / "compute").glob("*.png"))
        storage_icons = list((icons_dir / "storage").glob("*.png"))
        print(f"   Found {len(compute_icons)} compute icons")
        print(f"   Found {len(storage_icons)} storage icons")

    print("\n[COMPLETE] Icon loading tests completed!")

except Exception as e:
    print(f"Error during testing: {e}")
    import traceback

    traceback.print_exc()
