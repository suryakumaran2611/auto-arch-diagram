#!/usr/bin/env python3
"""Check comprehensive service mappings."""
import json
from pathlib import Path

mappings_file = Path(__file__).parent / "comprehensive_service_mappings.json"
with open(mappings_file) as f:
    data = json.load(f)

for provider, services in data.items():
    print(f"{provider}: {len(services)} services")
    # Show first 20 for each
    for key, val in list(services.items())[:20]:
        print(f"  {key}: {val}")
    print()
