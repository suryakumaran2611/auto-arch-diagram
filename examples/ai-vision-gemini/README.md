# Google Gemini Vision Integration Demo

This example demonstrates how to use Google Gemini Vision models to automatically critique, refine, and enhance architecture diagrams generated from Infrastructure as Code.

---

## 🚀 Quick Start with Gemini

### 1. Obtain a Google Gemini API Key
Get a free API key from **[Google AI Studio](https://aistudio.google.com)**.

### 2. Set the Environment Variable
```bash
export GEMINI_API_KEY="your-gemini-api-key"
# (Optionally store in ~/.config/auto-arch-diagram/gemini_key with chmod 600)
```

### 3. Generate the Architecture Diagram Suite
```bash
python tools/generate_arch_diagram.py \
  --changed-files examples/ai-vision-gemini/main.tf \
  --out-png examples/ai-vision-gemini/architecture.png \
  --out-svg examples/ai-vision-gemini/architecture.svg \
  --out-drawio examples/ai-vision-gemini/architecture.drawio \
  --out-html examples/ai-vision-gemini/architecture.html \
  --ai-enhance \
  --ai-backend gemini \
  --gemini-model gemini-1.5-flash
```

---

## 🤖 Supported Gemini Models

| Model | Description | Cost / Tier |
|:---|:---|:---:|
| `gemini-1.5-flash` *(Default)* | Ultra-fast multimodal model with high quality visual reasoning. | **Free Tier (15 RPM)** |
| `gemini-1.5-flash-8b` | Lightweight high-throughput vision model for rapid iteration. | **Free Tier** |
| `gemini-2.0-flash` | Next-generation multimodal model with enhanced spatial layout understanding. | **Free Tier** |
| `gemini-1.5-pro` | Flagship reasoning model for highly complex multi-cloud topologies. | Paid / Free Tier |

---

## ⚡ GitHub Actions Workflow Integration

Use the reusable workflow in your repository by providing the `GEMINI_API_KEY` secret:

```yaml
name: Architecture Diagram with Gemini AI

on:
  pull_request:
    paths:
      - '**/*.tf'
      - '**/*.bicep'
      - '**/template.yaml'

jobs:
  diagram:
    permissions:
      contents: read
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      direction: AUTO
      ai_enhance: true
      ai_backend: gemini
      gemini_model: gemini-1.5-flash
      comment_on_pr: true
    secrets:
      GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

---

## 📦 Emitted Artifacts

When `--ai-enhance` is enabled with Gemini, the generator creates a dedicated suite of AI-refined artifacts alongside the deterministic base outputs:
- `architecture-ai.png` / `architecture-ai.svg`: Raster and vector diagrams with AI-generated titles, subtitles, and operational context hints in the legend card.
- `architecture-ai.html`: Interactive studio with AI executive summaries and contextual tooltips.
- `architecture-ai.drawio`: Native draw.io diagram with Gemini operational tooltips and flow step labels.
- `architecture-ai.md`: Architectural insights report covering scalability, security posture, and dataflow stages.
