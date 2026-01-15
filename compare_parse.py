#!/usr/bin/env python3
import hcl2

data1 = hcl2.load(open("examples/terraform/custom-icons-demo/main.tf"))
data2 = hcl2.load(open("examples/terraform/mlops-multi-region-aws/main.tf"))

print(f"Custom icons resources: {len(data1.get('resource', []))}")
print(f"Multi-region resources: {len(data2.get('resource', []))}")
print(f"Multi-region providers: {len(data2.get('provider', []))}")
