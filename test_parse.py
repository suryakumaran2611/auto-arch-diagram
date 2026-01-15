#!/usr/bin/env python3
import hcl2
import sys

try:
    with open(sys.argv[1]) as f:
        data = hcl2.load(f)
    print(f"SUCCESS: Parsed {len(data)} top-level items")
    print(f"Keys: {list(data.keys())[:20]}")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
