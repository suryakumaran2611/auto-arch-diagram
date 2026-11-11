# GitLab CI/CD example gallery

Twelve complete, copy-pasteable pipelines covering every supported input and the
most common adoption scenarios.

Each folder contains:

- `.gitlab-ci.yml` — the pipeline to copy into your repository.
- `README.md` — what it demonstrates, required variables/secrets, expected
  outputs and customisation notes.

| # | Scenario | Best for | Template style |
| --- | --- | --- | --- |
| [01](01-minimal-remote/) | Minimal remote include | First-time setup, no GitLab publishing | `include: remote` |
| [02](02-component-all-inputs/) | Every component input | Reference / template for your own pipeline | Component |
| [03](03-terraform-ai-gemini/) | Terraform + Gemini MR review | AI-refined diagrams and sticky MR notes | Component |
| [04](04-monorepo-matrix/) | Monorepo matrix | One diagram per Terraform module | Component |
| [05](05-gitlab-pages/) | GitLab Pages | Publish the interactive HTML studio | Component |
| [06](06-self-hosted-airgapped/) | Self-hosted / air-gapped | Private mirrors and tagged runners | Vendored/remote |
| [07](07-openrouter-free/) | OpenRouter free models | Zero-cost AI refinement | Component |
| [08](08-output-formats/) | Output formats | Mermaid-only, full suite, custom paths | Component |
| [09](09-scheduled-full-scan/) | Nightly full scan | Scheduled regeneration | Component |
| [10](10-commit-diagrams-back/) | Commit diagrams back | Keep diagrams next to the IaC | Component |
| [11](11-advanced-iac-inputs/) | Advanced IaC inputs | planfile, graphfile, varfiles, workspace, source | Component |
| [12](12-layout-tuning/) | Layout tuning | Simplified view, badges, render engine, sizing | Component |

The smallest possible pipeline is also kept at
[`.gitlab-ci.yml`](.gitlab-ci.yml) in this folder.

---

## Before you start

### Requirements

- GitLab 14.x+ for the include template, 16.9+ for the CI/CD component.
- A Linux/Docker runner with `bash`, `git`, `python3` and network access to the
  tool repository. Windows runners are not supported by the shell scripts; use a
  Docker or WSL-backed runner.
- Graphviz is installed automatically by the templates
  (`install-system-packages: true`) or must already exist in a custom image.

### Remote include vs component

| | `include: remote` | Component |
| --- | --- | --- |
| GitLab version | 14.x+ | 16.9+ |
| Publish this repo to GitLab | Not required | Required (mirror + tag) |
| Configuration | `AUTO_ARCH_*` variables | Typed `inputs:` |
| Validation before the runner starts | No | Yes |
| Recommended for | Quick start, GitHub-hosted tool | Platform teams, version pinning |

The remote include reads:

```text
https://raw.githubusercontent.com/suryakumaran2611/auto-arch-diagram/main/ci/gitlab/auto-arch-diagram.gitlab-ci.yml
```

The component reference uses your own GitLab instance:

```yaml
include:
  - component: $CI_SERVER_FQDN/<group>/auto-arch-diagram/auto-arch-diagram@1.0.0
```

Replace `<group>` and the version with your mirror and release tag.

### Secrets (masked CI/CD variables)

| Variable | Scope | Used by |
| --- | --- | --- |
| `AUTO_ARCH_GITLAB_TOKEN` | `api` | Sticky merge request notes (optional) |
| `GEMINI_API_KEY` | — | `ai-backend: gemini` |
| `OPENROUTER_API_KEY` | — | `ai-backend: openrouter` |
| `AUTO_ARCH_PUSH_TOKEN` | `write_repository` | Example 10 only |
| `CI_JOB_TOKEN` | — | Not sufficient for MR notes; never used for notes |

All AI integrations degrade gracefully: missing keys or exhausted quotas leave
the standard outputs intact and do not fail the job.

---

## All component inputs

Every input is optional. Defaults are shown exactly as declared in
[`templates/auto-arch-diagram/template.yml`](../../templates/auto-arch-diagram/template.yml).

### Job placement and tooling

| Input | Default | Description |
| --- | --- | --- |
| `job-prefix` | `auto-arch-diagram` | Prefix for the generate and comment job names. |
| `stage` | `build` | Stage for both jobs. |
| `image` | `python:3.12` | Job image; must contain `git` and `python3`. |
| `install-system-packages` | `true` | Install Graphviz + Open Sans with `apt-get`. Disable for images that already include them. |
| `job-tags` | `[]` | Runner tags, for example `["self-hosted", "docker"]`. |
| `tool-repository` | GitHub URL | Git URL of the auto-arch-diagram checkout. Point at a mirror for air-gapped runners. |
| `tool-ref` | `main` | Branch, tag or commit SHA. Pin a tag in production. |

### Change detection

| Input | Default | Description |
| --- | --- | --- |
| `changed-files` | `''` | Explicit space/newline list; bypasses diff detection. |
| `iac-globs` | Terraform/Bicep/CFN/Pulumi/CDK globs | Patterns used to select changed files. |
| `iac-root` | `.` | Directory to scan. |
| `force-full` | `false` | Ignore change detection and scan every tracked IaC file. |
| `always-run` | `false` | Run on every pipeline, including feature-branch pushes. |

### Outputs

| Input | Default | Description |
| --- | --- | --- |
| `out-dir` | `artifacts` | Artifact directory (also the dotenv location). |
| `image-formats` | `png,jpg,svg` | Raster/vector formats; use `none` for Mermaid/Markdown only. |
| `out-md` | `<out-dir>/architecture-diagram.md` | Custom Markdown path. |
| `out-mmd` | `<out-dir>/architecture-diagram.mmd` | Custom Mermaid path. |
| `out-png` | `<out-dir>/architecture-diagram.png` | Custom PNG path. |
| `out-jpg` | `<out-dir>/architecture-diagram.jpg` | Custom JPEG path. |
| `out-svg` | `<out-dir>/architecture-diagram.svg` | Custom SVG path. |
| `out-drawio` | `<out-dir>/architecture-diagram.drawio` | Editable draw.io; `__disabled__` skips it. |
| `out-html` | `<out-dir>/architecture-diagram.html` | Interactive HTML; `__disabled__` skips it. |
| `artifacts-expire-in` | `1 week` | GitLab artifact retention. |

### Rendering and model shape

| Input | Default | Description |
| --- | --- | --- |
| `direction` | `AUTO` | `AUTO`, `LR`, `RL`, `TB`, `BT`. |
| `render-layout` | `lanes` | `lanes` (category lanes) or `providers` (brand grouping). |
| `render-bg` | `transparent` | `transparent` or `white` for PNG/SVG. |
| `edge-color` | `#4B5563` | Graphviz edge colour. |
| `edge-penwidth` | `1.3` | Edge line width. |
| `edge-arrowsize` | `0.8` | Arrow head size. |
| `fontsize` | empty | Integer base font size. |
| `iconsize` | empty | Integer icon size in pixels. |
| `render-engine` | `auto` | `auto` (3-stage postprocess + `neato -n2`), `neato`, `dot`. |
| `simplified` | `false` | Executive view that strips plumbing resources. |
| `expand-badges` | `false` | Security groups/NSGs become standalone nodes. |
| `no-consolidate` | `false` | Keep every repeated resource instance. |

### Advanced IaC inputs

| Input | Default | Description |
| --- | --- | --- |
| `planfile` | `''` | Pre-generated `terraform show -json` plan. Skips HCL parsing. |
| `graphfile` | `''` | Pre-generated `terraform graph` DOT file. Skips HCL parsing. |
| `varfile` | `''` | Newline/space-separated variable files, passed as repeated `--varfile`. |
| `workspace` | `default` | Terraform workspace name. |
| `source` | `''` | Clone and diagram a remote Git repo (`https://host/repo.git//subfolder`). |
| `annotate` | `''` | Custom numbered-flow annotations YAML. |

### AI vision refinement

| Input | Default | Description |
| --- | --- | --- |
| `ai-enhance` | `false` | Generate the extra `*-ai.*` suite. |
| `ai-backend` | `auto` | `auto`, `gemini`, `openrouter`, `ollama`, `bedrock`, `restapi`. |
| `gemini-model` | `gemini-3.8-flash` | Gemini free-tier vision model. |
| `openrouter-model` | empty | Empty keeps live $0 + vision ranking. |
| `ollama-model` | `llama3` | Used when `ai-backend: ollama`. |
| `ai-iterations` | empty | 1–5 refinement iterations; early-stops on plateau. |

### Merge request notes

| Input | Default | Description |
| --- | --- | --- |
| `mr-comment` | `true` | Post/update a sticky MR note. Requires `AUTO_ARCH_GITLAB_TOKEN` (`api` scope). |

---

## All include-template variables

The include template maps every input to an `AUTO_ARCH_*` variable. Variables
not listed here are optional pass-throughs read directly by the generator.

| Variable | Default |
| --- | --- |
| `AUTO_ARCH_IMAGE` | `python:3.12` |
| `AUTO_ARCH_INSTALL_SYSTEM_PACKAGES` | `true` |
| `AUTO_ARCH_STAGE` | `build` |
| `AUTO_ARCH_TOOL_REPOSITORY` | GitHub URL |
| `AUTO_ARCH_TOOL_REF` | `main` |
| `AUTO_ARCH_TOOL_DIR` | `.auto-arch-diagram-tool` |
| `AUTO_ARCH_CHANGED_FILES` | empty |
| `AUTO_ARCH_IAC_GLOBS` | built-in glob list |
| `AUTO_ARCH_IAC_ROOT` | `.` |
| `AUTO_ARCH_OUT_DIR` | `artifacts` |
| `AUTO_ARCH_IMAGE_FORMATS` | `png,jpg,svg` |
| `AUTO_ARCH_OUT_MD` … `AUTO_ARCH_OUT_HTML` | derived from `AUTO_ARCH_OUT_DIR` |
| `AUTO_ARCH_DIRECTION` | `AUTO` |
| `AUTO_ARCH_RENDER_LAYOUT` | `lanes` |
| `AUTO_ARCH_RENDER_BG` | `transparent` |
| `AUTO_ARCH_RENDER_ENGINE` | `auto` |
| `AUTO_ARCH_EDGE_COLOR` | `#4B5563` |
| `AUTO_ARCH_EDGE_PENWIDTH` | `1.3` |
| `AUTO_ARCH_EDGE_ARROWSIZE` | `0.8` |
| `AUTO_ARCH_FONTSIZE` / `AUTO_ARCH_ICONSIZE` | empty |
| `AUTO_ARCH_SIMPLIFIED` | `false` |
| `AUTO_ARCH_EXPAND_BADGES` | `false` |
| `AUTO_ARCH_NO_CONSOLIDATE` | `false` |
| `AUTO_ARCH_PLANFILE` | empty |
| `AUTO_ARCH_GRAPHFILE` | empty |
| `AUTO_ARCH_VARFILE` | empty |
| `AUTO_ARCH_WORKSPACE` | `default` |
| `AUTO_ARCH_SOURCE` | empty |
| `AUTO_ARCH_ANNOTATE` | empty |
| `AUTO_ARCH_AI_ENHANCE` | `false` |
| `AUTO_ARCH_AI_BACKEND` | `auto` |
| `AUTO_ARCH_GEMINI_MODEL` | `gemini-3.8-flash` |
| `AUTO_ARCH_OPENROUTER_MODEL` | empty |
| `AUTO_ARCH_OLLAMA_MODEL` | `llama3` |
| `AUTO_ARCH_AI_ITERATIONS` | empty |
| `AUTO_ARCH_FORCE_FULL` | `false` |
| `AUTO_ARCH_ALWAYS_RUN` | `false` |
| `AUTO_ARCH_MR_COMMENT` | `true` |
| `AUTO_ARCH_ARTIFACTS_EXPIRE_IN` | `1 week` |

The generator also honours `GEMINI_MODEL` / `OPENROUTER_MODEL` directly when the
component is not used.

---

## Consuming generated outputs

Every run writes `ci.env` and exposes it as a dotenv report:

```yaml
publish:
  stage: deploy
  needs:
    - job: auto-arch-diagram
      artifacts: true
  script:
    - test -f "$AUTO_ARCH_MD"
    - test -f "$AUTO_ARCH_PNG"
    - echo "HTML studio: $AUTO_ARCH_HTML"
```

Available variables: `AUTO_ARCH_HAS_CHANGES`, `AUTO_ARCH_OUT_DIR`,
`AUTO_ARCH_SUMMARY_FILE`, `AUTO_ARCH_CHANGED_FILES`, `AUTO_ARCH_MD`,
`AUTO_ARCH_MMD`, `AUTO_ARCH_PNG`, `AUTO_ARCH_JPG`, `AUTO_ARCH_SVG`,
`AUTO_ARCH_DRAWIO`, `AUTO_ARCH_HTML`.

---

## Testing an example locally

You can lint a pipeline without a GitLab instance using
[`gitlab-ci-local`](https://github.com/firecow/gitlab-ci-local):

```bash
npm install -g gitlab-ci-local
cd examples/gitlab-ci/01-minimal-remote
gitlab-ci-local --variable CI_PIPELINE_SOURCE=web
```

For the generator itself:

```bash
python tools/generate_arch_diagram.py \
  --changed-files examples/terraform/custom-icons-demo/main.tf \
  --out-dir artifacts/manual-demo \
  --direction AUTO
```

---

## Full reference

- [GitLab CI/CD guide](../../docs/GITLAB_CI.md) — inputs, secrets, Pages,
  self-hosted runners, troubleshooting and GitHub→GitLab migration.
- [Component template](../../templates/auto-arch-diagram/template.yml)
- [Include template](../../ci/gitlab/auto-arch-diagram.gitlab-ci.yml)
- [Shared runner script](../../ci/gitlab/auto-arch-diagram.sh)
