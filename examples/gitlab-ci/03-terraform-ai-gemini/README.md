# 03 — Terraform + Gemini merge request review

Generates the standard diagram suite, an AI-refined `*-ai.*` suite, and a sticky
merge request note with the diagram inline.

## Pipeline

```yaml
include:
  - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@1.0.0
    inputs:
      iac-root: infra
      out-dir: artifacts/terraform
      image-formats: png,svg,drawio,html
      render-layout: providers
      ai-enhance: true
      ai-backend: gemini
      gemini-model: gemini-3.8-flash
      ai-iterations: '3'
      mr-comment: true
```

## Required CI/CD variables

| Variable | Type | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | Masked | Google AI Studio key; free tier is enough. |
| `AUTO_ARCH_GITLAB_TOKEN` | Masked, `api` scope | Post/update the sticky MR note. |

`CI_JOB_TOKEN` cannot create merge request notes, which is why a dedicated token
is used. Without it the comment job logs a warning and passes.

## What Gemini adds

- Executive title and operational subtitle.
- Resource labels and hover tooltips.
- Numbered flow steps over the data/control paths.
- Layout critique and spacing refinements.
- A Markdown review summary.

The output folder contains both the standard suite and the refined one:

```text
artifacts/terraform/
├── architecture-diagram.*        # standard
├── architecture-diagram-ai.*     # AI-refined
├── gitlab-ci-summary.md
└── ci.env
```

## Free-tier model behaviour

- Default: `gemini-3.8-flash`.
- Free fallbacks: `gemini-3.6-flash`, `gemini-3.5-flash-lite`,
  `gemini-3.1-flash-lite`, `gemini-flash-latest`, `gemini-flash-lite-latest`.
- Paid-only aliases (`gemini-pro-latest`) and deprecated `gemini-2.5-*` models
  are intentionally excluded.
- Quota exhaustion degrades gracefully: standard outputs remain valid and the job
  succeeds.
- `ai-iterations` accepts 1–5 and stops early when quality plateaus.

## Run it manually

```bash
GEMINI_API_KEY=... \
python tools/generate_arch_diagram.py \
  --changed-files examples/ai-vision-gemini/main.tf \
  --out-dir artifacts/gemini-demo \
  --ai-enhance --ai-backend gemini \
  --gemini-model gemini-3.8-flash
```

## Related examples

- [07 — OpenRouter free models](../07-openrouter-free/)
- [12 — Layout tuning](../12-layout-tuning/)
