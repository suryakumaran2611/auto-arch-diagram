#!/usr/bin/env python3
from pathlib import Path
import yaml

p = Path("examples/serverless-website/aws/cloudformation/template.yaml")
print(f"File: {p}")
print(f"Name: {p.name}")
print(f"Name lower: {p.name.lower()}")
print(f"Matches: {p.name.lower() in {'template.yml', 'template.yaml'}}")
print(f"Exists: {p.exists()}")

if p.exists():
    data = yaml.safe_load(p.read_text())
    print(f"Resources: {list(data.get('Resources', {}).keys())}")
