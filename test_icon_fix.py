#!/usr/bin/env python3
"""Test script to verify icon loading fixes"""

import sys
from pathlib import Path

# Add tools to path
repo_root = Path(__file__).resolve().parents[0]
tools_dir = repo_root / "tools"
sys.path.insert(0, str(tools_dir))

try:
    from generate_arch_diagram import _load_custom_icon, _icon_class_for

    # Test AWS Lambda icon loading
    print("Testing AWS Lambda icon loading...")
    lambda_icon = _load_custom_icon("aws_lambda")
    if lambda_icon:
        print("[PASS] AWS Lambda icon loaded successfully")
    else:
        print("[FAIL] AWS Lambda icon not found")

    # Test AWS S3 icon loading
    print("\nTesting AWS S3 icon loading...")
    s3_icon = _load_custom_icon("aws_s3")
    if s3_icon:
        print("[PASS] AWS S3 icon loaded successfully")
    else:
        print("[FAIL] AWS S3 icon not found")

    # Test AWS EC2 icon loading
    print("\nTesting AWS EC2 icon loading...")
    ec2_icon = _load_custom_icon("aws_ec2")
    if ec2_icon:
        print("[PASS] AWS EC2 icon loaded successfully")
    else:
        print("[FAIL] AWS EC2 icon not found")

    # Test icon class resolution
    print("\nTesting icon class resolution...")
    lambda_class = _icon_class_for("aws_lambda")
    s3_class = _icon_class_for("aws_s3")

    print(f"Lambda class: {lambda_class}")
    print(f"S3 class: {s3_class}")

    print("\nIcon loading tests completed.")

except Exception as e:
    print(f"Error during testing: {e}")
    import traceback

    traceback.print_exc()
