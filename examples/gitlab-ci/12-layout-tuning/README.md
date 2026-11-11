# 12 — Layout tuning

Two complementary renders: an executive view and a detailed view. Shows the
rendering, model-shape and sizing inputs together.

## Executive view

```yaml
      job-prefix: diagram-executive
      simplified: true
      render-layout: providers
      direction: LR
      render-bg: white
      fontsize: '11'
      iconsize: '64'
      render-engine: auto
```

- `simplified: true` strips plumbing resources (VPCs, subnets, route tables,
  security groups) for a board-level view.
- `render-layout: providers` groups by cloud brand.
- `render-bg: white` is best for slides and printing.
- `fontsize`/`iconsize` are integer overrides; omit them for the automatic
  complexity-based sizing.

## Detailed view

```yaml
      job-prefix: diagram-detailed
      simplified: false
      render-layout: lanes
      direction: TB
      expand-badges: true
      no-consolidate: true
      render-engine: dot
      edge-color: '#334155'
      edge-penwidth: '1.6'
      edge-arrowsize: '1.0'
```

- `expand-badges: true` renders security groups/NSGs as standalone nodes.
- `no-consolidate: true` keeps every repeated resource instance.
- `render-engine: dot` uses plain Graphviz `dot` instead of the 3-stage
  postprocess + `neato -n2` pipeline.
- Edge colour/width/arrow size accept Graphviz values.

## Important: do not combine contradictory flags

`simplified: true` removes security groups, so `expand-badges: true` has nothing
to expand. Keep them in separate jobs, as this example does.

## Input reference

| Input | Values | Effect |
| --- | --- | --- |
| `direction` | `AUTO`, `LR`, `RL`, `TB`, `BT` | Graph orientation |
| `render-layout` | `lanes`, `providers` | Category lanes vs brand grouping |
| `render-bg` | `transparent`, `white` | PNG/SVG background |
| `render-engine` | `auto`, `neato`, `dot` | Graphviz pipeline |
| `simplified` | boolean | Executive view |
| `expand-badges` | boolean | Security groups as nodes |
| `no-consolidate` | boolean | Keep every instance |
| `edge-color` | any Graphviz colour | Edge stroke |
| `edge-penwidth` | number | Edge width |
| `edge-arrowsize` | number | Arrow head size |
| `fontsize` | integer | Base label size |
| `iconsize` | integer pixels | Icon size |

## Which engine should I use?

| Engine | Best for |
| --- | --- |
| `auto` (default) | Most diagrams; 3-stage geometry + GVPR postprocess + `neato -n2` |
| `neato` | Direct `neato` render without the postprocess stages |
| `dot` | Hierarchical graphs, fastest, least postprocessing |

If a diagram looks cramped, try `render-engine: auto` with `fontsize: 10` and
`iconsize: 48`. If it is too sparse, raise `iconsize` to 64–80.

## Expected output

Each job uploads its own folder:

```text
diagram-executive -> artifacts/layout/executive/
diagram-detailed  -> artifacts/layout/detailed/
```

## Which version should I use?

This example pins the current release (`@2.1.3`). If you are not sure which
version to use, reference the `main` branch instead:

```yaml
include:
  - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@main
    inputs:
      # ...same inputs as above
```

`@main` always picks up the latest code and works without publishing a release
tag to your mirror, so it is the easiest way to get started. It is not
reproducible, though: pipeline behaviour can change without a commit in your
repository. Move to a release tag (or a commit SHA) before you depend on it in
production.

## Related examples

- [08 — Output formats](../08-output-formats/)
- [02 — Every component input](../02-component-all-inputs/)
