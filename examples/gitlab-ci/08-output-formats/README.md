# 08 — Output formats

Shows how to generate Mermaid/Markdown only, the complete suite, or a custom set
of output paths.

## Variants

### A. Mermaid + Markdown only (fastest)

```yaml
      job-prefix: diagram-mermaid-only
      out-dir: artifacts/mermaid
      image-formats: none
      out-drawio: __disabled__
      out-html: __disabled__
```

### B. Complete suite

```yaml
      job-prefix: diagram-full
      out-dir: artifacts/full
      image-formats: png,jpg,svg
      out-drawio: ''
      out-html: ''
```

### C. Custom paths

```yaml
      job-prefix: diagram-custom-paths
      out-dir: artifacts/custom
      image-formats: png,jpg,svg
      out-md: artifacts/custom/docs/architecture.md
      out-mmd: artifacts/custom/docs/architecture.mmd
      out-png: artifacts/custom/images/architecture.png
      out-jpg: artifacts/custom/images/architecture.jpg
      out-svg: artifacts/custom/images/architecture.svg
      out-drawio: artifacts/custom/editable/architecture.drawio
      out-html: artifacts/custom/studio/index.html
```

## Format matrix

| `image-formats` | `out-drawio` | `out-html` | Result |
| --- | --- | --- | --- |
| `none` | `__disabled__` | `__disabled__` | `.md` + `.mmd` only |
| `png` | `__disabled__` | `__disabled__` | Markdown, Mermaid, PNG |
| `png,svg` | `''` | `''` | Markdown, Mermaid, PNG, SVG, draw.io, HTML |
| `png,jpg,svg` | `''` | `__disabled__` | Full raster/vector suite + draw.io, no HTML |
| `png,jpg,svg` | `''` | `''` | Complete suite |

## Important: custom paths must stay inside `out-dir`

The component uploads only `$[[ inputs.out-dir ]]/`. If you point an output
outside that folder, the file is generated but not attached to the pipeline.
The custom example keeps every path under `artifacts/custom/`.

## Disabling an export

Set the path to the sentinel value:

```yaml
      out-drawio: __disabled__
      out-html: __disabled__
```

Leaving the input empty (`''`) keeps the default path and enables the export.

## Why Mermaid-only is useful

- Very fast on large repositories.
- The `.md` embeds the Mermaid diagram and can be committed or rendered by
  GitLab's Markdown viewer.
- No Graphviz or image tooling is required.

## Expected artifacts

```text
artifacts/mermaid/       architecture-diagram.md, .mmd, ci.env
artifacts/full/          .md, .mmd, .png, .jpg, .svg, .drawio, .html, ci.env
artifacts/custom/        docs/, images/, editable/, studio/, ci.env
```

## Related examples

- [05 — GitLab Pages](../05-gitlab-pages/)
- [10 — Commit diagrams back](../10-commit-diagrams-back/)
