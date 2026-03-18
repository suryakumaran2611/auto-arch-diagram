# Multi-Region Active-Passive (AWS)

This example demonstrates multi-region architecture rendering in the generator.

## What It Shows

- Primary region in us-east-1
- DR region in us-west-2
- Region-specific VPC and subnet layout
- Cross-region connectivity with VPC peering
- Cross-region database replication intent

## Generate Diagram

```bash
python tools/generate_arch_diagram.py \
  --iac-root examples/terraform/multi-region-active-passive \
  --out-png examples/terraform/multi-region-active-passive/architecture-diagram.png \
  --out-mmd examples/terraform/multi-region-active-passive/architecture-diagram.mmd \
  --direction AUTO
```
