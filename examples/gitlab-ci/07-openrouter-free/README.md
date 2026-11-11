# 07 — OpenRouter free models

Zero-cost AI refinement using OpenRouter's live catalog of `$0` vision models.
No model is hardcoded: the client ranks the current free vision catalog at
runtime and walks it on rate limits or outages.

## Pipeline

```yaml
include:
  - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@1.0.0
    inputs:
      iac-root: infra
      out-dir: artifacts/openrouter
      image-formats: png,svg,drawio,html
      ai-enhance: true
      ai-backend: openrouter
      ai-iterations: '2'
```

## Required CI/CD variable

| Variable | Type | Purpose |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Masked | Free OpenRouter key. |

Without a key the standard outputs are still generated; only the `*-ai.*` suite
is skipped.

## How free-only enforcement works

- Only models whose prompt **and** completion prices are exactly `0` qualify.
- Image input must be supported.
- Special-purpose models (safety, moderation, embeddings, rerankers, speech,
  music/audio) are filtered out.
- A model override is still validated: pointing `openrouter-model` at a paid
  model is refused rather than silently billed.
- The ranking prefers stable instruction-tuned models, then the largest context
  window.

Current free vision candidates at the time of writing include:

```text
thinkingmachines/inkling-2-small:free
nvidia/nemotron-3.5-super-vl:free
google/gemma-4-31b-it:free
google/gemma-4-26b-a4b-it:free
dots-studio/dots-3-note-preview:free
nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
openrouter/free
```

Treat this as illustrative, not a contract: the list is fetched live and changes
over time.

## Optional model override

Leave `openrouter-model` empty to use the ranking. To pin a model, it must be a
current `$0` vision model:

```yaml
      openrouter-model: google/gemma-4-31b-it:free
```

## Quotas and failure behaviour

- The OpenRouter free tier currently allows roughly 50 vision requests per day.
- On `429` the client tries the next ranked model, then the next, and only fails
  the AI step after the ranked list is exhausted.
- The working model is remembered in a cache file and reused on later runs.
- Standard diagrams are always produced.

## Output

```text
artifacts/openrouter/
├── architecture-diagram.*        # standard
├── architecture-diagram-ai.*     # OpenRouter-refined
├── gitlab-ci-summary.md
└── ci.env
```

## Related examples

- [03 — Terraform + Gemini](../03-terraform-ai-gemini/)
- [12 — Layout tuning](../12-layout-tuning/)
