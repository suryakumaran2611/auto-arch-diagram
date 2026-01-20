#!/usr/bin/env python3
"""Test icon loading directly"""

import sys
from pathlib import Path

# Add tools to path
repo_root = Path(__file__).resolve().parents[1]
tools_dir = repo_root / "tools"
sys.path.insert(0, str(tools_dir))

from tools.generate_arch_diagram import _icon_class_for, _load_custom_icon

# Test the functions directly
print("Testing _load_custom_icon...")
result1 = _load_custom_icon("aws_athena_workgroup")
print(f"_load_custom_icon('aws_athena_workgroup') = {result1}")

print("\nTesting _icon_class_for...")
result2 = _icon_class_for("aws_athena_workgroup")
print(f"_icon_class_for('aws_athena_workgroup') = {result2}")

print("\nTesting with lambda...")
result3 = _icon_class_for("aws_lambda_function")
print(f"_icon_class_for('aws_lambda_function') = {result3}")

print("\nTesting with Glue...")
result4 = _icon_class_for("aws_glue_catalog_database")
print(f"_icon_class_for('aws_glue_catalog_database') = {result4}")
