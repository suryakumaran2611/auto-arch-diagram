# auto-arch-diagram

[![Python Tests](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/python-tests.yml/badge.svg)](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/python-tests.yml)
[![CodeQL](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/codeql.yml/badge.svg)](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/codeql.yml)
[![Dependency Review](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/dependency-review.yml)
[![Secret Scan](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/secret-scan.yml)
[![OSSF Scorecard](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/scorecard.yml/badge.svg)](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/scorecard.yml)

A GitHub PR “agent” that generates professional architecture diagrams from Infrastructure-as-Code (IaC) changes.

- PR comment output: Mermaid diagram (inline)
- Artifact output: PNG/SVG/JPEG diagrams rendered with professional cloud icons (via Graphviz + `diagrams`)
- Optional: opens a separate “diagram update PR” that commits generated diagrams back into your repo

## How it works

- A GitHub Actions workflow runs on PRs that change IaC files.
- It reads the changed IaC files (with light redaction + truncation).
- It generates a Mermaid `flowchart` diagram for inline viewing.
- It also renders a PNG/SVG diagram using official-style provider icons (via the `diagrams` + Graphviz libraries).
- It posts/updates a PR comment containing the Mermaid diagram and a link to the workflow run (where artifacts can be downloaded).

## Why this is useful

- Consistent review artifact: every IaC PR gets an architecture view without manual diagramming.
- Security-minded defaults: minimal permissions, safe `pull_request_target` pattern for “diagram PRs”, secret scanning.
- Reusable across repositories via `workflow_call`.

## Setup (no external AI)

1) Ensure the workflow exists:

- [.github/workflows/auto-arch-diagram.yml](.github/workflows/auto-arch-diagram.yml)

This repo also ships a reusable workflow that other repositories can call:

- [.github/workflows/reusable-auto-arch-diagram.yml](.github/workflows/reusable-auto-arch-diagram.yml)

Optional (commit diagrams into the repo via a separate “diagram update PR”):

- Set repository variable `AUTO_ARCH_CREATE_DIAGRAM_PR=true`
- Configure output locations in [.auto-arch-diagram.yml](.auto-arch-diagram.yml) under `publish.paths`.

2) Default generator mode is `static` (no external AI). It uses parsing libraries to infer dependencies and outputs a Mermaid diagram.

3) The workflow installs Graphviz to render icon-based diagrams. If Graphviz is unavailable, the Mermaid diagram is still produced.

## Security scans and checks

This repo includes “shift-left” security checks that run on PRs and/or on a schedule:

- Code scanning: CodeQL ([.github/workflows/codeql.yml](.github/workflows/codeql.yml))
- Dependency diffs: Dependency Review ([.github/workflows/dependency-review.yml](.github/workflows/dependency-review.yml))
- Secret scanning: gitleaks ([.github/workflows/secret-scan.yml](.github/workflows/secret-scan.yml))
- Supply-chain posture: OSSF Scorecard ([.github/workflows/scorecard.yml](.github/workflows/scorecard.yml))
- Python security tooling in CI: `pip-audit` + `bandit` ([.github/workflows/python-tests.yml](.github/workflows/python-tests.yml))
- Automated updates: Dependabot ([.github/dependabot.yml](.github/dependabot.yml))

## Optional: AI mode

If you want higher-quality diagrams across more IaC styles, you can enable AI mode.

1) Set repo variable:

- `AUTO_ARCH_MODE=ai`

2) Add an OpenAI key as a repository secret:

- `OPENAI_API_KEY`

3) (Optional) Set the model via repo variable:

- `AUTO_ARCH_MODEL` (defaults to `gpt-4o-mini`)

## Supported IaC file types

The workflow triggers on common IaC file patterns, including:

- Terraform: `*.tf`, `*.tfvars`, `*.hcl`
- Bicep: `*.bicep`
- CloudFormation: `template.yml`, `template.yaml`, `*.cfn.yml`, `*.cfn.yaml`, `*.cfn.json`
- Pulumi: `Pulumi.*.(yaml|yml|json|ts|py)`
- CDK: `*.cdk.ts`, `*.cdk.py`

Adjust the patterns in the workflow if your repo layout differs.

## Use in any repo (reusable workflow)

### Common knobs (formats + paths)

- `image_formats`: `png,jpg,svg` (default), a subset like `png,svg`, or `none` to skip icon rendering.
- `out_dir`: where the workflow writes outputs (and uploads artifacts from).

If you want to fully control file names/locations, you can also override:

- `out_md`, `out_mmd`, `out_png`, `out_jpg`, `out_svg`

Example: Mermaid-only (fastest, no Graphviz required):

```yaml
with:
  mode: static
  image_formats: none
  out_dir: artifacts
```

Example: Custom output paths:

```yaml
with:
  mode: static
  image_formats: png,svg
  out_dir: build/diagrams
  out_md: docs/architecture/architecture-diagram.md
  out_mmd: docs/architecture/architecture-diagram.mmd
  out_png: docs/architecture/architecture-diagram.png
  out_svg: docs/architecture/architecture-diagram.svg
```

### Use as a composite action (advanced)

If you already have your own workflow and want a single step (instead of `workflow_call`), you can use the composite action:

```yaml
- name: Generate architecture diagram
  uses: suryakumaran2611/auto-arch-diagram@v1
  with:
    changed_files: ${{ steps.changed.outputs.all_changed_files }}
    mode: static
    direction: LR
    image_formats: png,svg
    out_dir: artifacts
```

Versioning:

- Create a release by pushing a semver tag like `v1.0.0`.
- The workflow also maintains a moving major tag like `v1` (so callers can pin `@v1`).

## Release checklist

- Update [CHANGELOG.md](CHANGELOG.md) (move items from Unreleased into the new version).
- Ensure CI is green (tests + CodeQL + dependency review).
- Tag and push: `git tag vX.Y.Z` then `git push origin vX.Y.Z`.
- Confirm the GitHub Release was created and `vX` tag moved.

Create `.github/workflows/auto-arch-diagram.yml` in your repo and call the reusable workflow from this repo.

PR comment + artifacts:

```yaml
name: Auto Architecture Diagram

on:

  pull_request:
    types: [opened, synchronize, reopened]
    paths:
      - '**/*.tf'
      - '**/*.tfvars'
      - '**/*.hcl'
      - '**/*.bicep'
      - '**/*.cfn.yaml'
      - '**/*.cfn.yml'
      - '**/*.cfn.json'
      - '**/template.yaml'
      - '**/template.yml'
      - '**/Pulumi.yaml'
      - '**/Pulumi.yml'
      - '**/Pulumi.*.yaml'
      - '**/Pulumi.*.yml'
      - '**/Pulumi.*.json'
      - '**/Pulumi.*.ts'
      - '**/Pulumi.*.py'
      - '**/*.cdk.ts'
      - '**/*.cdk.py'

jobs:
  diagram:
    permissions:
      contents: read
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
    with:
      mode: static
      direction: LR
      render_layout: lanes
      render_bg: transparent
      # Choose which images to render (png,jpg,svg) or disable with 'none'
      image_formats: png,svg
      # Where artifacts are written + uploaded from
      out_dir: artifacts
      publish_enabled: false
      comment_on_pr: true
      create_diagram_pr: false
```

Optional diagram update PR (commits `publish.paths.*` back into your repo):

- Add repo variable `AUTO_ARCH_CREATE_DIAGRAM_PR=true`
- Add `pull_request_target` trigger (write permissions) in the same workflow file.

Full single-file example (recommended):

```yaml
name: Auto Architecture Diagram

on:

  pull_request:
    types: [opened, synchronize, reopened]
    paths:
      - '**/*.tf'
      - '**/*.tfvars'
      - '**/*.hcl'
      - '**/*.bicep'
      - '**/*.cfn.yaml'
      - '**/*.cfn.yml'
      - '**/*.cfn.json'
      - '**/template.yaml'
      - '**/template.yml'
      - '**/Pulumi.yaml'
      - '**/Pulumi.yml'
      - '**/Pulumi.*.yaml'
      - '**/Pulumi.*.yml'
      - '**/Pulumi.*.json'
      - '**/Pulumi.*.ts'
      - '**/Pulumi.*.py'
      - '**/*.cdk.ts'
      - '**/*.cdk.py'

  pull_request_target:
    types: [opened, synchronize, reopened]
    paths:
      - '**/*.tf'
      - '**/*.tfvars'
      - '**/*.hcl'
      - '**/*.bicep'
      - '**/*.cfn.yaml'
      - '**/*.cfn.yml'
      - '**/*.cfn.json'
      - '**/template.yaml'
      - '**/template.yml'
      - '**/Pulumi.yaml'
      - '**/Pulumi.yml'
      - '**/Pulumi.*.yaml'
      - '**/Pulumi.*.yml'
      - '**/Pulumi.*.json'
      - '**/Pulumi.*.ts'
      - '**/Pulumi.*.py'
      - '**/*.cdk.ts'
      - '**/*.cdk.py'

jobs:
  comment:
    if: ${{ github.event_name == 'pull_request' }}
    permissions:
      contents: read
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
    with:
      mode: static
      direction: LR
      render_layout: lanes
      render_bg: transparent
      image_formats: png,svg
      out_dir: artifacts
      publish_enabled: false
      comment_on_pr: true
      create_diagram_pr: false

  diagram_pr:
    if: ${{ github.event_name == 'pull_request_target' && vars.AUTO_ARCH_CREATE_DIAGRAM_PR == 'true' }}
    permissions:
      contents: write
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
    with:
      mode: static
      direction: LR
      render_layout: lanes
      render_bg: transparent
      image_formats: png,svg
      out_dir: artifacts
      publish_enabled: true
      comment_on_pr: false
      create_diagram_pr: true
```

To control which files get committed by the diagram-update PR, configure `publish.paths` in `.auto-arch-diagram.yml`:

```yaml
publish:

  enabled: true
  paths:
    md: docs/architecture/architecture-diagram.md
    mmd: docs/architecture/architecture-diagram.mmd
    png: docs/architecture/architecture-diagram.png
    jpg: docs/architecture/architecture-diagram.jpg
    svg: docs/architecture/architecture-diagram.svg

render:
  layout: lanes
  bg: transparent
```

## Local run (optional)

From the repo root:

1) Install deps:

```bash
python -m pip install -r requirements.txt
```

2) Run the generator:

```bash
python tools/generate_arch_diagram.py --changed-files "path/to/main.tf path/to/vpc.tf"
```

To run with AI mode locally:

```bash
python -m pip install -r requirements-ai.txt
set OPENAI_API_KEY=...  # PowerShell: $env:OPENAI_API_KEY="..."
set AUTO_ARCH_MODE=ai
python tools/generate_arch_diagram.py --changed-files "path/to/main.tf path/to/vpc.tf"
```

Output:

- `artifacts/architecture-diagram.md` (PR comment body)
- `artifacts/architecture-diagram.mmd` (raw mermaid)
- `artifacts/architecture-diagram.png` (rendered diagram with icons, if Graphviz+diagrams available)
- `artifacts/architecture-diagram.jpg` (rendered diagram with icons; note: JPEG has no transparency)
- `artifacts/architecture-diagram.svg` (rendered diagram with icons, if Graphviz+diagrams available)

## Unit tests

- CI runs on every push/PR: [.github/workflows/python-tests.yml](.github/workflows/python-tests.yml)
- Locally in WSL:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

## Security notes

- The generator performs basic redaction of likely-secret assignments (e.g. `password=...`, `token: ...`).
- Still, do not store secrets directly in IaC files.
- For large changes, the tool truncates file contents to keep prompts bounded.

Diagram PR workflow:

- Uses `pull_request_target` so it can open a PR back to the base repo.
- Checks out the generator code from the base branch, and checks out PR contents into a separate `pr/` folder (read-only usage).

## Current static support

- Terraform (`*.tf`, `*.hcl`): parses resources and draws edges from inferred references/depends_on.
- CloudFormation (`template.yml|yaml`, `*.cfn.yml|yaml|json`): uses Resources + Ref/GetAtt/Sub/DependsOn.
- Azure Bicep (`*.bicep`): best-effort parsing of `resource`, `dependsOn`, and `parent`.
- Pulumi YAML (`Pulumi.yaml|yml`): parses `resources`, `options.dependsOn`, and `${resource.property}` references.

Other IaC types (like CDK programs) are detected by the workflow but may not render a full diagram in static mode yet.

## Notes on “professional icons”

GitHub PR comments can render Mermaid inline, but they do not reliably support embedding arbitrary external icon sets inside Mermaid nodes.
To keep the diagram professional, the workflow produces PNG/SVG artifacts rendered with provider icon sets using the `diagrams` library.

By default, icon rendering uses an “industry standard” layout (category lanes, orthogonal edges, compact spacing, transparent PNG/SVG background). You can override this in [.auto-arch-diagram.yml](.auto-arch-diagram.yml) under `render` (for example, switch to provider-first grouping).

## Example outputs

Pre-generated diagrams (Mermaid + PNG + SVG) are checked in under `examples/` so you can see the expected style:

- [examples/terraform/aws-basic/architecture-diagram.png](examples/terraform/aws-basic/architecture-diagram.png)
- [examples/terraform/multi-cloud-complex/architecture-diagram.png](examples/terraform/multi-cloud-complex/architecture-diagram.png)

### Showcase: complex multi-cloud + serverless website

This repo includes a set of security-first “serverless website” reference implementations across providers and IaC styles:

- [examples/serverless-website/README.md](examples/serverless-website/README.md)
- Terraform examples (best icon rendering):
  - [examples/serverless-website/aws/terraform/main.tf](examples/serverless-website/aws/terraform/main.tf)
  - [examples/serverless-website/azure/terraform/main.tf](examples/serverless-website/azure/terraform/main.tf)
  - [examples/serverless-website/gcp/terraform/main.tf](examples/serverless-website/gcp/terraform/main.tf)
  - [examples/serverless-website/oci/terraform/main.tf](examples/serverless-website/oci/terraform/main.tf)
  - [examples/serverless-website/ibm/terraform/main.tf](examples/serverless-website/ibm/terraform/main.tf)

And a multi-cloud Terraform example that stresses layout and lane grouping:

- [examples/terraform/multi-cloud-complex/main.tf](examples/terraform/multi-cloud-complex/main.tf)

Secure serverless website examples across providers/IaC:

- [examples/serverless-website/aws/terraform/main.tf](examples/serverless-website/aws/terraform/main.tf)
- [examples/serverless-website/aws/cloudformation/template.yaml](examples/serverless-website/aws/cloudformation/template.yaml)
- [examples/serverless-website/azure/bicep/main.bicep](examples/serverless-website/azure/bicep/main.bicep)
- [examples/serverless-website/gcp/terraform/main.tf](examples/serverless-website/gcp/terraform/main.tf)

To regenerate these locally (without touching `publish.paths` outputs), run with `AUTO_ARCH_PUBLISH_ENABLED=false`.

```bash
. .venv/bin/activate
AUTO_ARCH_PUBLISH_ENABLED=false python tools/regenerate_examples.py
```

## Future plans

- Improve static parsing coverage for additional IaC types (CDK, Pulumi programs, ARM/Bicep edge cases) while keeping “no external AI” as the default.
- Add optional diagram post-processing: de-duplication, legend generation, grouping heuristics, and better label/edge routing for very large graphs.
- Introduce caching to speed up repeated runs (same IaC inputs → same artifacts) and reduce workflow runtime.
- Expand outputs (optional): standalone HTML report, per-stack/per-module diagrams, and “diff view” (what changed between before/after).
- Provide an optional pre-commit hook / local CLI wrapper so contributors can generate diagrams before opening a PR.

