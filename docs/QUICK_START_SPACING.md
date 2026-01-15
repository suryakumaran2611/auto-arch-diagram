# Quick Start: Dynamic Spacing Configuration

## Use Auto Mode (Recommended)

The simplest and most effective approach - spacing automatically adjusts based on your infrastructure complexity:

```yaml
# .auto-arch-diagram.yml
render:
  graph:
    pad: auto
    nodesep: auto
    ranksep: auto
```

**That's it!** The system will:
- Analyze your diagram (nodes, edges, clusters)
- Calculate optimal spacing
- Apply intelligent edge routing
- Prevent overlaps and collisions

## Common Adjustments

### Too Compact? Increase Minimum Spacing

```yaml
render:
  graph:
    pad: auto
    nodesep: auto
    ranksep: auto
    min_nodesep: 0.35    # Default: 0.25
    min_ranksep: 0.85    # Default: 0.65
```

### Too Large? Reduce Complexity Scaling

```yaml
render:
  graph:
    pad: auto
    nodesep: auto
    ranksep: auto
    complexity_scale: 1.2    # Default: 1.5 (range: 1.0-2.0)
```

### Arrows Still Overlapping?

```yaml
render:
  graph:
    pad: auto
    nodesep: auto
    ranksep: auto
    edge_density_scale: 1.5    # Default: 1.2 (increase for denser diagrams)
    edge_routing: spline       # Try different routing: ortho | spline | curved
```

### Want Compact Layout?

```yaml
render:
  graph:
    pad: auto
    nodesep: auto
    ranksep: auto
    overlap_removal: compress    # Default: prism
    complexity_scale: 1.0        # Minimal scaling
```

## Manual Control

If you need exact values:

```yaml
render:
  graph:
    pad: 0.5
    nodesep: 0.4
    ranksep: 1.0
    # Auto-calculation disabled when using numbers
```

## Edge Routing Quick Reference

| Routing | Best For | Appearance |
|---------|----------|------------|
| `ortho` (default) | Architecture diagrams | 90° angles, professional |
| `spline` | Organic layouts | Smooth curves |
| `polyline` | Simple diagrams | Straight lines with bends |
| `curved` | Presentations | Aesthetic curves |

## Overlap Removal Quick Reference

| Strategy | Best For | Speed |
|----------|----------|-------|
| `prism` (default) | Most diagrams | Fast |
| `scalexy` | Wide diagrams | Fast |
| `compress` | Large diagrams | Fast |
| `vpsc` | Complex constraints | Slow |

## Debug Mode

See what spacing is calculated:

```bash
export AUTO_ARCH_DEBUG=1
python3 tools/generate_arch_diagram.py ...
```

Output:
```
[Diagram Complexity] Nodes: 25, Edges: 38
[Diagram Complexity] Clusters: 5, Depth: 2
[Diagram Complexity] Avg edges/node: 1.52
[Spacing] pad=0.56, nodesep=0.43, ranksep=1.15
```

## Full Documentation

For comprehensive guide, see: [docs/DYNAMIC_SPACING.md](DYNAMIC_SPACING.md)
