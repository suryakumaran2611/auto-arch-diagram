# Dynamic Spacing System

## Overview

The auto-arch-diagram tool now features an intelligent **dynamic spacing system** that automatically adjusts diagram layout parameters based on infrastructure complexity. This ensures optimal visual clarity regardless of diagram size or complexity.

## How It Works

### Complexity Analysis

Before rendering, the system analyzes your infrastructure diagram across multiple dimensions:

1. **Node Count** - Number of resources in the diagram
2. **Edge Density** - Average connections per resource
3. **Cluster Count** - Number of provider/category groupings
4. **Nesting Depth** - Levels of cluster nesting
5. **Label Length** - Maximum resource name length
6. **Provider Diversity** - Number of different cloud providers

### Automatic Spacing Calculation

Based on these metrics, the system calculates optimal spacing parameters:

- **Pad**: Border padding around the entire diagram
- **Nodesep**: Horizontal spacing between nodes
- **Ranksep**: Vertical spacing between node ranks/levels

The spacing increases progressively as complexity grows, using weighted algorithms that consider:
- Edge density (prevents arrow overlaps)
- Cluster depth (prevents nested cluster collisions)
- Direction (LR vs TB layouts)

### Intelligent Edge Routing

Additional features prevent visual clutter:

- **Overlap removal** using Graphviz's prism algorithm
- **Dynamic separation** between clusters and edges
- **Edge crossing minimization**
- **Adaptive edge lengths** for high-density diagrams

## Configuration

### Auto Mode (Default)

By default, spacing is calculated automatically:

```yaml
# .auto-arch-diagram.yml
render:
  graph:
    pad: auto
    nodesep: auto
    ranksep: auto
```

### Manual Override

You can override specific values while keeping others automatic:

```yaml
render:
  graph:
    pad: 0.5          # Fixed padding
    nodesep: auto     # Auto horizontal spacing
    ranksep: auto     # Auto vertical spacing
```

### Advanced Tuning

Fine-tune the automatic calculation:

```yaml
render:
  graph:
    # Spacing calculation mode
    pad: auto
    nodesep: auto
    ranksep: auto
    
    # Minimum spacing values (base constraints)
    min_pad: 0.3
    min_nodesep: 0.25
    min_ranksep: 0.65
    
    # Complexity scaling factors
    complexity_scale: 1.5      # Overall complexity multiplier (1.0-2.0 recommended)
    edge_density_scale: 1.2    # Extra scaling for high edge density
    
    # Edge routing algorithm
    edge_routing: ortho        # ortho | spline | polyline | curved
    
    # Overlap removal strategy
    overlap_removal: prism     # prism | scalexy | compress | vpsc | ipsep | false
```

## Complexity Metrics

### Simple Diagrams
- **Nodes**: < 10
- **Edges/Node**: < 2
- **Clusters**: < 3
- **Result**: Minimal spacing, compact layout

**Spacing**: pad ~0.3, nodesep ~0.3, ranksep ~0.8

### Medium Diagrams
- **Nodes**: 10-30
- **Edges/Node**: 2-3
- **Clusters**: 3-7
- **Result**: Moderate spacing, balanced layout

**Spacing**: pad ~0.5, nodesep ~0.5, ranksep ~1.2

### Complex Diagrams
- **Nodes**: 30-50
- **Edges/Node**: 3-4
- **Clusters**: 7-10
- **Result**: Generous spacing, clear separation

**Spacing**: pad ~0.7, nodesep ~0.7, ranksep ~1.6

### Very Complex Diagrams
- **Nodes**: > 50
- **Edges/Node**: > 4
- **Clusters**: > 10
- **Result**: Maximum spacing, maximum clarity

**Spacing**: pad ~1.0, nodesep ~1.0, ranksep ~2.0

## Edge Routing Options

### Orthogonal (Default - `ortho`)
Best for: Architecture diagrams with clear hierarchies
- Clean 90-degree angles
- Professional appearance
- Works well with clusters

### Spline (`spline`)
Best for: Organic-looking diagrams
- Curved edges
- More compact
- Can overlap with text if spacing is too tight

### Polyline (`polyline`)
Best for: Simple, minimal diagrams
- Straight lines with bends
- Minimal space usage
- Fast rendering

### Curved (`curved`)
Best for: Presentation-quality diagrams
- Smooth bezier curves
- Aesthetically pleasing
- Requires more spacing

## Overlap Removal Strategies

### Prism (Default - `prism`)
- **Best for**: Most diagrams
- **Behavior**: Scales nodes apart using Voronoi algorithm
- **Speed**: Fast
- **Quality**: Excellent for clustered layouts

### Scale XY (`scalexy`)
- **Best for**: Wide diagrams
- **Behavior**: Scales separately in X and Y directions
- **Speed**: Fast
- **Quality**: Good for preventing horizontal overlap

### Compress (`compress`)
- **Best for**: Large diagrams
- **Behavior**: Compresses nodes into available space
- **Speed**: Fast
- **Quality**: Compact but may sacrifice some clarity

### VPSC (`vpsc`)
- **Best for**: Complex constraint requirements
- **Behavior**: Variable placement with separation constraints
- **Speed**: Slower
- **Quality**: Highest quality for complex graphs

### IPSEP (`ipsep`)
- **Best for**: Simple diagrams
- **Behavior**: Incremental separation
- **Speed**: Very fast
- **Quality**: Basic overlap prevention

### False (`false`)
- **Best for**: Pre-arranged layouts
- **Behavior**: No overlap removal
- **Speed**: Fastest
- **Quality**: May have overlaps

## Debugging

Enable debug output to see calculated spacing values:

```bash
export AUTO_ARCH_DEBUG=1
python3 tools/generate_arch_diagram.py ...
```

Output example:
```
[Diagram Complexity] Nodes: 42, Edges: 67
[Diagram Complexity] Clusters: 8, Depth: 2
[Diagram Complexity] Avg edges/node: 1.60
[Spacing] pad=0.68, nodesep=0.52, ranksep=1.35
```

## Examples

### Simple AWS Infrastructure
```yaml
# Uses minimal spacing automatically
# Nodes: 5, Edges: 6
# Result: Compact, easy to read
```

### Multi-Cloud Architecture
```yaml
# Auto-detects complexity and increases spacing
# Nodes: 35, Edges: 52
# Result: Generous spacing prevents overlaps
```

### Microservices with High Connectivity
```yaml
# Detects high edge density
# Applies edge_density_scale multiplier
# Result: Extra spacing for arrow clarity
```

## Migration from Fixed Spacing

If you previously used fixed spacing values:

**Before:**
```yaml
render:
  graph:
    pad: 0.3
    nodesep: 0.25
    ranksep: 0.65
```

**After (Recommended):**
```yaml
render:
  graph:
    pad: auto
    nodesep: auto
    ranksep: auto
    # Optionally adjust minimum constraints
    min_pad: 0.3
    min_nodesep: 0.25
    min_ranksep: 0.65
```

## Best Practices

1. **Start with defaults** - Auto mode works well for most cases
2. **Adjust minimums** - If diagrams are too compact, increase `min_*` values
3. **Tune complexity_scale** - Increase for more aggressive spacing (1.5-2.0)
4. **Choose appropriate edge_routing** - `ortho` for professional, `spline` for compact
5. **Test with real data** - Generate diagrams and iterate on settings
6. **Use debug mode** - Understand what spacing is being applied

## Troubleshooting

### Arrows Still Overlapping
- Increase `edge_density_scale` from 1.2 to 1.5
- Increase `min_nodesep` and `min_ranksep` by 20-30%
- Try `edge_routing: spline` for better curve handling

### Diagram Too Large
- Decrease `complexity_scale` from 1.5 to 1.2
- Use `overlap_removal: compress` for tighter packing
- Consider `concentrate: true` to bundle parallel edges

### Labels Overlapping Edges
- Increase `min_ranksep` to create more vertical space
- Use `edge_routing: ortho` for predictable edge paths
- Increase `min_pad` for more border space

### Clusters Overlapping
- Increase `complexity_scale` to 1.8 or 2.0
- Check `max_cluster_depth` in debug output
- Increase `min_ranksep` significantly for deep nesting

## Performance Considerations

Dynamic spacing adds minimal overhead:
- **Analysis**: < 10ms for most diagrams
- **Calculation**: < 5ms
- **Total Impact**: < 1% of rendering time

The Graphviz rendering itself remains the performance bottleneck.

## Future Enhancements

Potential improvements for future versions:
- ML-based spacing prediction
- Layout-specific optimization (LR vs TB vs RL vs BT)
- Custom spacing profiles (compact, balanced, spacious)
- Interactive spacing preview
- Per-cluster spacing overrides
