#!/usr/bin/env python3
import hcl2
import sys
from pathlib import Path

def _terraform_resources_from_hcl(parsed):
    resources = {}
    blocks = parsed.get("resource")
    if not blocks:
        print(f"No 'resource' key found. Keys: {list(parsed.keys())}")
        return resources

    print(f"Found resource blocks: {len(blocks)} items")
    # python-hcl2 returns resource blocks as a list of dicts.
    for i, block in enumerate(blocks):
        print(f"Block {i}: type={type(block)}")
        if not isinstance(block, dict):
            continue
        for r_type, r_body in block.items():
            print(f"  Resource type: {r_type}, body type: {type(r_body)}")
            if isinstance(r_body, dict):
                # { "aws_vpc": {"main": {...}} }
                for name, attrs in r_body.items():
                    if isinstance(attrs, dict):
                        resources[f"{r_type}.{name}"] = attrs
                        print(f"    Added: {r_type}.{name}")
            elif isinstance(r_body, list):
                # Sometimes: { "aws_vpc": [ {"main": {...}} ] }
                for entry in r_body:
                    if not isinstance(entry, dict):
                        continue
                    for name, attrs in entry.items():
                        if isinstance(attrs, dict):
                            resources[f"{r_type}.{name}"] = attrs
                            print(f"    Added: {r_type}.{name}")
    return resources

try:
    with open(sys.argv[1]) as f:
        data = hcl2.load(f)
    print(f"Parsed successfully!")
    print(f"Top-level keys: {list(data.keys())}")
    resources = _terraform_resources_from_hcl(data)
    print(f"\nTotal resources found: {len(resources)}")
    print(f"First 10: {list(resources.keys())[:10]}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
