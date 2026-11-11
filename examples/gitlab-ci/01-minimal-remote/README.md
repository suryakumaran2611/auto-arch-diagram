# 01 — Minimal remote include

The smallest working pipeline. It uses the template hosted on GitHub, so nothing
needs to be copied into your repository and nothing needs to be published to
GitLab.

## Pipeline

```yaml
stages:
  - build

include:
  - remote: https://raw.githubusercontent.com/suryakumaran2611/auto-arch-diagram/main/ci/gitlab/auto-arch-diagram.gitlab-ci.yml

variables:
  AUTO_ARCH_IAC_ROOT: infra
  AUTO_ARCH_OUT_DIR: artifacts/architecture
```

## How to use it

1. Copy `.gitlab-ci.yml` to the root of your repository.
2. Set `AUTO_ARCH_IAC_ROOT` to the folder that contains your Terraform/Bicep/
   CloudFormation/Pulumi/CDK files.
3. Commit and open a merge request.

## What runs

- `auto-arch-diagram:generate` runs on merge request pipelines, pushes to the
  default branch and manual pipelines.
- `auto-arch-diagram:comment` runs on merge requests and is non-blocking. It
  posts a sticky note when `AUTO_ARCH_GITLAB_TOKEN` is configured.
- Artifacts are uploaded from `artifacts/architecture/`: Markdown, Mermaid, PNG,
  JPEG, SVG, draw.io and interactive HTML unless `AUTO_ARCH_IMAGE_FORMATS`
  changes that.

## Requirements

- GitLab 14.x or newer.
- A Linux/Docker runner with network access to GitHub and the tool's Python
  dependencies.
- No secrets are required for the basic diagram. AI refinement and MR notes are
  opt-in.

## Customise

Add any variable from
[the variable reference](../README.md#all-include-template-variables), for
example:

```yaml
variables:
  AUTO_ARCH_IAC_ROOT: infra
  AUTO_ARCH_OUT_DIR: artifacts/architecture
  AUTO_ARCH_IMAGE_FORMATS: png,svg,drawio,html
  AUTO_ARCH_DIRECTION: LR
  AUTO_ARCH_RENDER_BG: white
```

## Expected output

```text
artifacts/architecture/
├── architecture-diagram.md
├── architecture-diagram.mmd
├── architecture-diagram.png
├── architecture-diagram.jpg
├── architecture-diagram.svg
├── architecture-diagram.drawio
├── architecture-diagram.html
├── gitlab-ci-summary.md
└── ci.env
```

## Which version should I use?

The remote include above already tracks the `main` branch, so there is nothing to
pin and no tag to publish - this is the recommended starting point.

When you need reproducible pipelines, point the same `include` at a release tag
instead:

```yaml
include:
  - remote: https://raw.githubusercontent.com/suryakumaran2611/auto-arch-diagram/v2.1.3/ci/gitlab/auto-arch-diagram.gitlab-ci.yml
```

Or vendor the template into your repository and review it like application code
(see [06 - Self-hosted / air-gapped](../06-self-hosted-airgapped/)).
