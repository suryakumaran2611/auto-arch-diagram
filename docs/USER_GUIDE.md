# 🏗️ Auto Architecture Diagram — Comprehensive User Guide

Transform Infrastructure-as-Code (Terraform, CloudFormation, Bicep, Pulumi) into interactive HTML studios, editable native draw.io diagrams, crisp vector SVGs, and AI-enhanced architecture artifacts.

---

## 📑 Table of Contents

1. [Platform Overview](#-platform-overview)
2. [Quick Start](#-quick-start)
   - [GitHub Actions Workflow](#1-github-actions-reusable-workflow-recommended)
   - [Local CLI Generation](#2-local-cli-generation)
3. [Output Formats Matrix](#-output-formats-matrix)
   - [Interactive HTML Studio (`.html`)](#1-interactive-html-architecture-studio---out-html)
   - [Native draw.io Vector Exporter (`.drawio`)](#2-native-drawio-vector-exporter---out-drawio)
   - [AI-Enhanced Multi-Format Suite (`*-ai.*`)](#3-ai-enhanced-multi-format-suite---ai-enhance)
   - [Scalable Vector SVG (`.svg`)](#4-scalable-vector-svg---out-svg)
   - [High-Res PNG & JPEG (`.png`, `.jpg`)](#5-high-res-png--jpeg)
   - [Mermaid & Markdown (`.mmd`, `.md`)](#6-mermaid--markdown-embeds)
4. [CI/CD Automation & GitHub Integration](#-cicd-automation--github-integration)
   - [Sticky PR Comments](#sticky-pull-request-comments)
   - [Automated Diagram PRs](#automatic-diagram-pull-requests)
   - [Direct Repository Auto-Commit](#direct-repository-auto-commit)
   - [Force Updates](#force-diagram-updates)
5. [Confluence Publishing & Image Replacement](#-confluence-publishing--image-replacement)
   - [Workflow Configuration](#confluence-workflow-setup)
   - [Marker-Based Image Replacement](#marker-based-image-replacement)
   - [Multi-Environment Architecture Pages](#multi-environment-publishing)
6. [Model Context Protocol (MCP) Server for AI Assistants](#-model-context-protocol-mcp-server)
   - [Claude Desktop / Cursor / Antigravity Setup](#configuring-mcp-clients)
   - [Exposed MCP Tools](#mcp-tools-reference)
7. [Multi-Cloud & Structured Tiering](#-multi-cloud--structured-tiering)
8. [Full CLI Reference](#-full-cli-reference)
9. [Enterprise Showcase Gallery](#-enterprise-showcase-gallery)
10. [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 🌟 Platform Overview

The **Auto Architecture Diagram** suite automatically extracts, categorizes, and renders cloud topologies directly from your Infrastructure-as-Code files.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Infrastructure as Code                          │
│   Terraform (.tf) • CloudFormation (YAML) • Bicep • Pulumi • CDK       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Static / Plan Analysis
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Intelligent Layout Pipeline                       │
│  • 3-Stage Neato Post-Processing Engine                                │
│  • Obstacle-Avoiding Orthogonal Corridor Router                        │
│  • Multi-Cloud Palette & Brand Border Accents (AWS, Azure, GCP, OCI)   │
│  • 100% Guaranteed Bottom-Centered Unified Legend Card                 │
└──────┬───────────────────┬───────────────────┬───────────────────┬─────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  🌐 HTML     │    │  📊 draw.io  │    │  🤖 AI Suite │    │  📐 SVG/PNG  │
│  Studio      │    │  Vectors     │    │  Insights    │    │  Vectors     │
│  • Path Trace│    │  • 2026 Pack │    │  • Vision Opt│    │  • Base64    │
│  • Impact Map│    │  • Jumps     │    │  • Steps     │    │  • Centered  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## 🚀 Quick Start

### 1. GitHub Actions Reusable Workflow (Recommended)

Create `.github/workflows/auto-arch-diagram.yml` in your repository:

```yaml
name: Architecture Diagram

on:
  pull_request:
    paths:
      - '**/*.tf'
      - '**/*.bicep'
      - '**/template.yaml'
      - '**/template.yml'
  workflow_dispatch:
    inputs:
      force_update:
        description: 'Force diagram generation even if no IaC files changed'
        type: boolean
        default: false

jobs:
  diagram:
    permissions:
      contents: read
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      direction: AUTO                 # Intelligent layout selection
      image_formats: png,svg,drawio,html
      comment_on_pr: true             # Post interactive sticky comment on PR
      force_full: ${{ github.event.inputs.force_update || false }}
```

---

### 2. Local CLI Generation

#### Environment Setup (WSL Ubuntu / Linux / macOS)
```bash
# Clone and enter repo
git clone https://github.com/suryakumaran2611/auto-arch-diagram.git
cd auto-arch-diagram

# Setup Python 3.12+ virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
sudo apt-get install -y graphviz  # macOS: brew install graphviz
```

#### Run Generator
```bash
# Generate complete multi-format suite from a Terraform directory:
python tools/generate_arch_diagram.py \
  --changed-files examples/terraform/mlops-multi-region-aws/main.tf \
  --out-png artifacts/architecture.png \
  --out-svg artifacts/architecture.svg \
  --out-drawio artifacts/architecture.drawio \
  --out-html artifacts/architecture.html \
  --direction AUTO
```

---

## 📦 Output Formats Matrix

### 1. 🌐 Interactive HTML Architecture Studio (`--out-html`)
Generates a standalone, zero-CDN, offline-ready HTML studio file with embedded SVG vectors and metadata.

- **Path Tracing & Blast-Radius Impact Analysis**: Click any node to highlight upstream dependencies, downstream consumers, and direct network edges.
- **Dynamic Tier Filter Matrix**: Live toggle chips for Compute, Storage, Database, Security, Containers, and Integration layers.
- **Radar Mini-Map & Smooth Pan/Zoom**: Fast, fluid navigation across dense 100+ node architectures.
- **Resource Inspector Drawer**: Click nodes to inspect Terraform resource types, attributes, provider categories, and custom tags.
- **In-Browser Export Studio**: Export custom filtered views directly to high-res PNG or JSON metadata.

👉 **[Launch Live Demo (MLOps Multi-Region AWS)](https://suryakumaran2611.github.io/auto-arch-diagram/demos/mlops-aws.html)**

---

### 2. 📊 Native draw.io Vector Exporter (`--out-drawio`)
Generates native `.drawio` files using official vector shape packs that can be edited in [draw.io](https://app.diagrams.net).

- **Official Editable Shapes**: Uses official AWS 2026 (`mxgraph.aws4.*`), Azure SVG (`img/lib/azure2/*`), and GCP (`mxgraph.gcp2.*`) shape packs — fully editable, no embedded raster PNGs.
- **Obstacle-Avoiding Orthogonal Corridor Routing**: Connectors route strictly through free whitespace gutters, **never crossing over or cutting through node icons or labels**.
- **Bridge Arc Line Jumps (`jumpStyle=arc;jumpSize=6`)**: Crisp line bridges at every crossing to eliminate 4-way intersection ambiguity.
- **AWS Group Frames & Centered Legend**: Official `mxgraph.aws4.group` containers with bottom-centered legend cards.

👉 **[Open Live draw.io Diagram in diagrams.net](https://viewer.diagrams.net/?highlight=0000ff&edit=_blank&layers=1&nav=1#Uhttps%3A%2F%2Fraw.githubusercontent.com%2Fsuryakumaran2611%2Fauto-arch-diagram%2Fmain%2Fdocs%2Fdemos%2Fmlops-multi-cloud.drawio)**

---

### 3. 🤖 AI-Enhanced Multi-Format Suite (`--ai-enhance`)
Runs an optional vision critique loop using **Google Gemini** or **OpenRouter free models** to critique layout density, generate executive subtitles, and add operational context.

- **Dual Provider Support**:
  - **Google Gemini Vision** (`--ai-backend gemini`): Uses Google's fast, free-tier vision models (`gemini-1.5-flash` by default, or `gemini-2.0-flash`, `gemini-1.5-flash-8b`, `gemini-1.5-pro`). Get your free API key at [Google AI Studio](https://aistudio.google.com).
  - **OpenRouter Free Tier** (`--ai-backend openrouter`): Strict $0 budget ranking that loops through active free vision models.
- **Vision-Assisted Layout Refinement**: Vision models inspect diagram density and suggest ranksep/nodesep adjustments to eliminate visual clutter.
- **Executive Titles & Numbered Flows**: Enriches diagrams with executive subtitles, numbered operational flow badges, and IaC review hints.
- **Dedicated Output Suite**: Emits `*-ai.png`, `*-ai.svg`, `*-ai.html`, `*-ai.drawio`, and `*-ai.md` alongside deterministic base outputs.

```bash
# Run with Google Gemini Vision:
export GEMINI_API_KEY="your-gemini-api-key"
python tools/generate_arch_diagram.py --changed-files path/to/main.tf \
  --out-png out/architecture.png --out-html out/architecture.html --out-drawio out/architecture.drawio \
  --ai-enhance --ai-backend gemini --gemini-model gemini-1.5-flash

# Run with OpenRouter:
export OPENROUTER_API_KEY="your-openrouter-key"
python tools/generate_arch_diagram.py --changed-files path/to/main.tf \
  --out-png out/architecture.png --out-html out/architecture.html --out-drawio out/architecture.drawio \
  --ai-enhance --ai-backend openrouter
```

#### Managing & Changing API Keys Locally

You can store and rotate API keys locally using persistent configuration files (recommended) or environment variables:

##### Option 1: Persistent Key Files (Recommended)
Key files are stored in `~/.config/auto-arch-diagram/` with `0600` permissions. They remain outside git tracking and work seamlessly without setting shell variables every time.

```bash
# Ensure secure directory exists
mkdir -p ~/.config/auto-arch-diagram && chmod 700 ~/.config/auto-arch-diagram

# 1. Google Gemini Key:
# To set or update:
echo "YOUR_GEMINI_API_KEY" > ~/.config/auto-arch-diagram/gemini_key
chmod 600 ~/.config/auto-arch-diagram/gemini_key

# 2. OpenRouter Key:
# To set or update:
echo "YOUR_OPENROUTER_API_KEY" > ~/.config/auto-arch-diagram/openrouter_key
chmod 600 ~/.config/auto-arch-diagram/openrouter_key
```

> **Manual Editing:** You can view or change the keys at any time using your favorite editor:
> ```bash
> nano ~/.config/auto-arch-diagram/gemini_key
> nano ~/.config/auto-arch-diagram/openrouter_key
> ```

##### Option 2: Environment Variables
```bash
# Session export
export GEMINI_API_KEY="your-gemini-key"
export OPENROUTER_API_KEY="your-openrouter-key"

# Permanent bash/zsh export
echo 'export GEMINI_API_KEY="your-gemini-key"' >> ~/.bashrc
source ~/.bashrc
```

**Resolution Hierarchy:** Environment Variables > Secure Key Files (`~/.config/auto-arch-diagram/`).

---

### 4. 📐 Scalable Vector SVG (`--out-svg`)
- High-contrast vector graphics with embedded high-resolution base64 icon assets.
- Single-provider category lanes and official provider brand accents (AWS `#FF9900`, Azure `#0078D4`, GCP `#4285F4`, OCI `#C74634`, IBM `#0F62FE`).
- 100% Guaranteed Bottom-Centered connectors legend table.

---

### 5. 🖼️ High-Res PNG & JPEG
- Sharp raster images with antialiased typography (**Open Sans Bold**).
- Pure white canvas with subtle category subcluster borders (`#CBD5E1`).

---

### 6. 🧜‍♀️ Mermaid & Markdown Embeds
- Generates native Mermaid `.mmd` flowcharts and GitHub Flavored Markdown `.md` embed reports.

---

## ⚡ CI/CD Automation & GitHub Integration

### Sticky Pull Request Comments

When `comment_on_pr: true` is enabled, the action automatically posts and updates a sticky comment on the PR containing:
1. Direct high-res diagram preview.
2. Formatted resource summary (added/modified resources).
3. Collapsible architectural breakdown table by category and cloud provider.
4. Links to download `.drawio` and launch the Interactive HTML Studio.

```yaml
jobs:
  comment:
    permissions:
      contents: read
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      direction: AUTO
      image_formats: png,svg,drawio,html
      comment_on_pr: true
```

---

### Automatic Diagram Pull Requests

Automatically generate and open a PR with updated diagrams in your repository:

```yaml
jobs:
  diagram_pr:
    if: github.event_name == 'pull_request_target'
    permissions:
      contents: write
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      create_diagram_pr: true
      publish_enabled: true
      diagram_pr_branch_prefix: 'auto-arch-diagram/update'
```

---

### Direct Repository Auto-Commit

Commit generated diagrams directly to the default branch on push:

```yaml
on:
  push:
    branches: [main]

jobs:
  diagram_commit:
    permissions:
      contents: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      auto_commit_artifacts: true
      create_diagram_pr: false
      publish_enabled: true
```

---

### Force Diagram Updates

To regenerate diagrams even when no IaC files have changed:
1. **Repository Variable**: Set `AUTO_ARCH_FORCE_UPDATE = true` in Repository Settings → Variables.
2. **Manual Dispatch**: Select "Force architecture diagram update" checkbox in GitHub Actions UI.
3. **Workflow Input**: Pass `force_full: true` in your workflow invocation.

---

## 📑 Confluence Publishing & Image Replacement

Automatically upload or replace architecture diagrams in Atlassian Confluence documentation pages.

### Confluence Workflow Setup

```yaml
jobs:
  publish_docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: suryakumaran2611/auto-arch-diagram@v1
        with:
          iac_globs: 'terraform/**/*.tf'
          publish_enabled: true
          publish_confluence: true
          confluence_url: ${{ secrets.CONFLUENCE_URL }}
          confluence_user: ${{ secrets.CONFLUENCE_USER }}
          confluence_token: ${{ secrets.CONFLUENCE_TOKEN }}
          confluence_page_id: '123456789'
          confluence_replace: true
          confluence_image_marker: '<!-- auto-arch-diagram:prod-architecture.png -->'
```

### Marker-Based Image Replacement
Place an HTML comment marker in your Confluence page source where the diagram should live:
```html
<!-- auto-arch-diagram:prod-architecture.png -->
<p><img src="architecture-diagram.png" /></p>
<!-- auto-arch-diagram:prod-architecture.png -->
```
The action will replace only the content between the matching markers, preserving all surrounding text, headers, and tables.

### Multi-Environment Publishing
Use distinct markers for multiple environments on a single Confluence wiki page:
- Staging: `<!-- auto-arch-diagram:staging-architecture.png -->`
- Production: `<!-- auto-arch-diagram:prod-architecture.png -->`
- DR / Disaster Recovery: `<!-- auto-arch-diagram:dr-architecture.png -->`

---

## 🤖 Model Context Protocol (MCP) Server

The built-in Model Context Protocol (MCP) server allows AI coding agents (Claude Desktop, Cursor, VS Code, Antigravity) to query and generate architecture diagrams interactively.

### Configuring MCP Clients

Add to your `claude_desktop_config.json` or `mcp.json`:

```json
{
  "mcpServers": {
    "auto-arch-diagram": {
      "command": "python3",
      "args": ["/path/to/auto-arch-diagram/tools/mcp_server.py"]
    }
  }
}
```

### MCP Tools Reference

| Tool Name | Parameters | Description |
|:---|:---|:---|
| `list_resources` | `changed_files`, `iac_root` | Lists all detected cloud resources, types, and categories. |
| `explain_graph` | `changed_files`, `iac_root` | Returns a natural language summary of the architectural connectivity and topology. |
| `generate_diagram` | `changed_files`, `iac_root`, `formats`, `direction` | Triggers diagram generation across specified formats (`png`, `svg`, `drawio`, `html`). |

---

## ☁️ Multi-Cloud & Structured Tiering

- **Universal Multi-Cloud**: Renders AWS, Azure, Google Cloud, Oracle Cloud (OCI), and IBM Cloud simultaneously on a single unified canvas.
- **Brand Palette Borders**:
  - AWS: `#FF9900` (Orange)
  - Azure: `#0078D4` (Blue)
  - GCP: `#4285F4` (Google Blue)
  - OCI: `#C74634` (Red)
  - IBM: `#0F62FE` (Carbon Blue)
- **Automatic Category Subclusters**: Uncontained resources are cleanly organized into `Security`, `Compute`, `Storage`, `Integration`, and `Management` subclusters with `#CBD5E1` borders and `#FFFFFF` background.
- **Guaranteed Centered Bottom Legend**: A clean HTML table centered at the bottom of the diagram categorizing all edge types and resource classes.

---

## 🛠️ Full CLI Reference

```
usage: generate_arch_diagram.py [-h] [--changed-files FILES] [--iac-root DIR]
                                [--direction {AUTO,LR,TB,RL,BT}]
                                [--out-png FILE] [--out-svg FILE]
                                [--out-jpg FILE] [--out-drawio FILE]
                                [--out-html FILE] [--out-md FILE]
                                [--out-mmd FILE] [--render-engine {auto,neato,dot}]
                                [--fontsize INT] [--iconsize INT]
                                [--simplified] [--expand-badges]
                                [--no-consolidate] [--planfile PLAN_JSON]
                                [--graphfile GRAPH_DOT] [--varfile PATH]
                                [--ai-enhance]
```

### Key CLI Flags
- `--changed-files <files>`: Space/newline-separated list of changed IaC files.
- `--out-html <file>`: Output path for the Interactive HTML Architecture Studio.
- `--out-drawio <file>`: Output path for native editable draw.io diagrams.
- `--ai-enhance`: Enable vision-assisted layout critique loop (Gemini or OpenRouter free models).
- `--ai-backend <auto|gemini|openrouter|ollama|bedrock>`: Vision provider backend (default `auto`).
- `--gemini-model <model>`: Google Gemini vision model name (default: `gemini-1.5-flash`).
- `--openrouter-model <model>`: OpenRouter vision model override.

---

## 🌟 Enterprise Showcase Gallery

| Architecture | Cloud Providers | Formats | Live Previews |
|:---|:---|:---:|:---|
| **Enterprise MLOps Multi-Region Platform** | AWS | PNG • SVG • draw.io • HTML | [🌐 Interactive HTML Studio](https://suryakumaran2611.github.io/auto-arch-diagram/demos/mlops-aws.html) • [📊 Open draw.io](https://viewer.diagrams.net/?highlight=0000ff&edit=_blank&layers=1&nav=1#Uhttps%3A%2F%2Fraw.githubusercontent.com%2Fsuryakumaran2611%2Fauto-arch-diagram%2Fmain%2Fdocs%2Fdemos%2Fmlops-aws.drawio) |
| **Secure Enterprise 3-Tier Web Platform** | AWS | PNG • SVG • draw.io • HTML | [🌐 Interactive HTML Studio](https://suryakumaran2611.github.io/auto-arch-diagram/demos/multi-tier-web-app.html) • [📊 Open draw.io](https://viewer.diagrams.net/?highlight=0000ff&edit=_blank&layers=1&nav=1#Uhttps%3A%2F%2Fraw.githubusercontent.com%2Fsuryakumaran2611%2Fauto-arch-diagram%2Fmain%2Fdocs%2Fdemos%2Fmulti-tier-web-app.drawio) |
| **Hybrid Multi-Cloud Data Analytics** | AWS + Azure + GCP | PNG • SVG • draw.io • HTML | [🌐 Interactive HTML Studio](https://suryakumaran2611.github.io/auto-arch-diagram/demos/mlops-multi-cloud.html) • [📊 Open draw.io](https://viewer.diagrams.net/?highlight=0000ff&edit=_blank&layers=1&nav=1#Uhttps%3A%2F%2Fraw.githubusercontent.com%2Fsuryakumaran2611%2Fauto-arch-diagram%2Fmain%2Fdocs%2Fdemos%2Fmlops-multi-cloud.drawio) |
| **Serverless Event Pipeline (Custom Icons)** | AWS + Custom Icons | PNG • SVG • draw.io • HTML | [🌐 Interactive HTML Studio](https://suryakumaran2611.github.io/auto-arch-diagram/demos/custom-icons-demo.html) • [📊 Open draw.io](https://viewer.diagrams.net/?highlight=0000ff&edit=_blank&layers=1&nav=1#Uhttps%3A%2F%2Fraw.githubusercontent.com%2Fsuryakumaran2611%2Fauto-arch-diagram%2Fmain%2Fdocs%2Fdemos%2Fcustom-icons-demo.drawio) |
| **Dual-VPC Transit & Peering Mesh** | AWS | PNG • SVG • draw.io • HTML | [🌐 Interactive HTML Studio](https://suryakumaran2611.github.io/auto-arch-diagram/demos/vpc-peering-multi-subnet.html) • [📊 Open draw.io](https://viewer.diagrams.net/?highlight=0000ff&edit=_blank&layers=1&nav=1#Uhttps%3A%2F%2Fraw.githubusercontent.com%2Fsuryakumaran2611%2Fauto-arch-diagram%2Fmain%2Fdocs%2Fdemos%2Fvpc-peering-multi-subnet.drawio) |
| **CloudFormation Production Web Stack** | AWS CloudFormation | PNG • SVG • draw.io • HTML | [🌐 Interactive HTML Studio](https://suryakumaran2611.github.io/auto-arch-diagram/demos/aws-cloudformation.html) • [📊 Open draw.io](https://viewer.diagrams.net/?highlight=0000ff&edit=_blank&layers=1&nav=1#Uhttps%3A%2F%2Fraw.githubusercontent.com%2Fsuryakumaran2611%2Fauto-arch-diagram%2Fmain%2Fdocs%2Fdemos%2Faws-cloudformation.drawio) |

---

## ❓ Troubleshooting & FAQ

### Frequently Asked Questions

**Q: Do I need cloud credentials or an active Terraform backend to generate diagrams?**
> **No.** The generator performs static parsing of your `.tf`, `.bicep`, or CloudFormation files directly. Alternatively, you can feed a pre-generated `terraform show -json` plan via `--planfile plan.json`.

**Q: How does the obstacle-avoiding corridor router work in draw.io exports?**
> The exporter calculates the exact absolute bounding boxes for all resource nodes and label blocks, builds whitespace gutter channels between columns and cluster frames, and routes connectors cleanly through those channels with bridge arc hops (`jumpStyle=arc`).

**Q: How do I test the workflow locally before pushing to GitHub?**
> Run the CLI command directly using Python in WSL or Linux:
> ```bash
> python tools/generate_arch_diagram.py --changed-files path/to/main.tf --out-png out.png --out-html out.html --out-drawio out.drawio
> ```

---

Built with ❤️ by [@suryakumaran2611](https://github.com/suryakumaran2611) • Licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)