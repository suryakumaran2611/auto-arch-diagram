# GitLab CI/CD setup

Generate architecture diagrams (Mermaid, Markdown, PNG, JPEG, SVG, draw.io and a
standalone interactive HTML studio) from Terraform, Bicep, CloudFormation,
Pulumi or CDK changes, straight from GitLab CI/CD.

The integration ships in two flavours:

| File | Use it when | GitLab version |
| --- | --- | --- |
| `templates/auto-arch-diagram/template.yml` | You mirror this repository to GitLab and want a versioned **CI/CD component** with typed inputs. | 16.9+ |
| `ci/gitlab/auto-arch-diagram.gitlab-ci.yml` | You want a one-line `include: remote` / `include: local` template configured through CI/CD variables. | 14.x+ |

Both call the same logic in `ci/gitlab/auto-arch-diagram.sh`, so features and
outputs are identical.

---

## Quick start

### Option A - remote include (no mirror required)

Create `.gitlab-ci.yml` in your repository:

```yaml
stages:
  - build

include:
  - remote: https://raw.githubusercontent.com/suryakumaran2611/auto-arch-diagram/main/ci/gitlab/auto-arch-diagram.gitlab-ci.yml

variables:
  AUTO_ARCH_IAC_ROOT: infra
  AUTO_ARCH_OUT_DIR: artifacts/architecture
```

The pipeline now runs `auto-arch-diagram:generate` on merge requests, pushes to
the default branch and manual runs. Diagrams are uploaded as job artifacts, and
`auto-arch-diagram:comment` posts a sticky merge request note when
`AUTO_ARCH_GITLAB_TOKEN` is configured.

### Option B - CI/CD component

Mirror this repository into a GitLab group (for example
`platform/auto-arch-diagram`), tag it (semantic versioning), and reference the
component:

```yaml
include:
  - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@1.0.0
    inputs:
      stage: build
      iac-root: infra
      out-dir: artifacts/architecture
      image-formats: png,jpg,svg
      direction: AUTO
```

Component inputs are validated when the pipeline is created, which makes
misconfiguration obvious before a runner starts. Set the component project as a
**CI/CD Catalog project** to make releases discoverable.

### Option C - vendored template

```yaml
include:
  - local: ci/gitlab/auto-arch-diagram.gitlab-ci.yml
```

Keep the file in your repository to pin and review it like application code.

---

## What the pipeline does

1. **Change detection** - reads the merge request diff base
   (`CI_MERGE_REQUEST_DIFF_BASE_SHA`), the push `CI_COMMIT_BEFORE_SHA`, or falls
   back to a full scan. Files are filtered by `AUTO_ARCH_IAC_GLOBS`.
2. **Tooling setup** - installs Graphviz + Open Sans (optional), clones the tool
   repository, installs Python dependencies and caches pip downloads.
3. **Generation** - runs the generator once and writes all requested formats.
4. **Validation** - the job fails if the Markdown or Mermaid outputs are missing
   or empty.
5. **Publishing** - artifacts are attached to the pipeline, a `ci.env` dotenv
   report exposes the output paths to later jobs, and an optional merge request
   note shows the diagram inline.

When the change set contains no IaC files, the job exits successfully, writes a
short summary, and sets `AUTO_ARCH_HAS_CHANGES=false` in `ci.env`.

---

## Component inputs

All inputs are optional except the component reference itself.

| Input | Default | Description |
| --- | --- | --- |
| `job-prefix` | `auto-arch-diagram` | Prefix for generated job names. |
| `stage` | `build` | Stage for the generate/comment jobs. |
| `image` | `python:3.12` | Job image. Must contain `git` and `python3`. |
| `install-system-packages` | `true` | `apt-get install graphviz fonts-open-sans`. Disable for images that already include them. |
| `job-tags` | `[]` | Runner tags, for example `["self-hosted", "docker"]`. |
| `tool-repository` | `https://github.com/suryakumaran2611/auto-arch-diagram.git` | Tool git URL. Point this at a mirror for air-gapped runners. |
| `tool-ref` | `main` | Branch, tag or commit SHA of the tool. Pin a tag or SHA in production. |
| `changed-files` | `''` | Explicit file list; bypasses diff detection. |
| `iac-globs` | Terraform/Bicep/CFN/Pulumi/CDK globs | Patterns used during change detection. |
| `iac-root` | `.` | Directory to scan. |
| `out-dir` | `artifacts` | Artifact directory. |
| `image-formats` | `png,jpg,svg` | Raster/vector formats; use `none` for Mermaid/Markdown only. |
| `out-md`, `out-mmd`, `out-png`, `out-jpg`, `out-svg` | `<out-dir>/architecture-diagram.*` | Custom output paths. |
| `out-drawio`, `out-html` | `<out-dir>/architecture-diagram.drawio/.html` | Editable vector + interactive HTML; set `__disabled__` to skip. |
| `direction` | `AUTO` | `AUTO`, `LR`, `RL`, `TB`, `BT`. |
| `render-layout` | `lanes` | `lanes` (category lanes) or `providers` (provider grouped). |
| `render-bg` | `transparent` | `transparent` or `white` for PNG/SVG. |
| `edge-color`, `edge-penwidth`, `edge-arrowsize` | `#4B5563`, `1.3`, `0.8` | Edge styling. |
| `fontsize`, `iconsize` | empty | Integer overrides. |
| `ai-enhance` | `false` | Generate the extra `*-ai.*` suite. |
| `ai-backend` | `auto` | `auto`, `gemini`, `openrouter`, `ollama`, `bedrock`, `restapi`. |
| `gemini-model` | `gemini-3.8-flash` | Gemini vision model (free tier). |
| `openrouter-model`, `ollama-model` | backend defaults | Model overrides. |
| `ai-iterations` | empty | 1-5 refinement iterations (early stop on plateau). |
| `force-full` | `false` | Ignore change detection and regenerate from every tracked IaC file. |
| `always-run` | `false` | Run on every pipeline, including feature-branch pushes. |
| `mr-comment` | `true` | Post/update a sticky merge request note. |
| `artifacts-expire-in` | `1 week` | GitLab artifact retention. |

### Variable equivalents (include template)

The include template uses variables instead of inputs. Every component input maps
to an `AUTO_ARCH_*` variable:

| Variable | Default |
| --- | --- |
| `AUTO_ARCH_IMAGE` | `python:3.12` |
| `AUTO_ARCH_INSTALL_SYSTEM_PACKAGES` | `true` |
| `AUTO_ARCH_TOOL_REPOSITORY` | `https://github.com/suryakumaran2611/auto-arch-diagram.git` |
| `AUTO_ARCH_TOOL_REF` | `main` |
| `AUTO_ARCH_CHANGED_FILES` | empty |
| `AUTO_ARCH_IAC_ROOT` | `.` |
| `AUTO_ARCH_IAC_GLOBS` | Terraform/Bicep/CFN/Pulumi/CDK globs |
| `AUTO_ARCH_OUT_DIR` | `artifacts` |
| `AUTO_ARCH_IMAGE_FORMATS` | `png,jpg,svg` |
| `AUTO_ARCH_OUT_MD`, `..._MMD`, `..._PNG`, `..._JPG`, `..._SVG`, `..._DRAWIO`, `..._HTML` | empty (derived from `AUTO_ARCH_OUT_DIR`) |
| `AUTO_ARCH_DIRECTION` | `AUTO` |
| `AUTO_ARCH_RENDER_LAYOUT` | `lanes` |
| `AUTO_ARCH_RENDER_BG` | `transparent` |
| `AUTO_ARCH_EDGE_COLOR` | `#4B5563` |
| `AUTO_ARCH_EDGE_PENWIDTH` | `1.3` |
| `AUTO_ARCH_EDGE_ARROWSIZE` | `0.8` |
| `AUTO_ARCH_FONTSIZE`, `AUTO_ARCH_ICONSIZE` | empty |
| `AUTO_ARCH_AI_ENHANCE` | `false` |
| `AUTO_ARCH_AI_BACKEND` | `auto` |
| `AUTO_ARCH_GEMINI_MODEL` | `gemini-3.8-flash` |
| `AUTO_ARCH_OPENROUTER_MODEL`, `AUTO_ARCH_OLLAMA_MODEL` | backend defaults |
| `AUTO_ARCH_AI_ITERATIONS` | empty |
| `AUTO_ARCH_FORCE_FULL` | `false` |
| `AUTO_ARCH_ALWAYS_RUN` | `false` |
| `AUTO_ARCH_MR_COMMENT` | `true` |
| `AUTO_ARCH_STAGE` | `build` |
| `AUTO_ARCH_ARTIFACTS_EXPIRE_IN` | `1 week` |

---

## Secrets and CI/CD variables

Add these as **masked** (and preferably **protected**) project or group
variables:

| Variable | Scope | Purpose |
| --- | --- | --- |
| `AUTO_ARCH_GITLAB_TOKEN` | `api` | Post/update the sticky merge request note. A project access token with `api` scope is enough; minimize its role. |
| `GEMINI_API_KEY` | - | Google Gemini AI refinement (`ai-enhance: true`, `ai-backend: gemini`). |
| `OPENROUTER_API_KEY` | - | OpenRouter AI refinement (free tier available). |

AI enhancement degrades gracefully: if the key or quota is missing, the standard
outputs are still generated and the job succeeds.

The merge request comment is best-effort. Missing token, wrong scope or API
errors are logged as warnings and the job continues.

> `CI_JOB_TOKEN` cannot create merge request notes, which is why a dedicated
> `api`-scoped token is used.

---

## Consuming the outputs

### Artifacts

Every run uploads `AUTO_ARCH_OUT_DIR/` (default `artifacts/`). Browse or download
it from the pipeline's **Job artifacts** view.

### dotenv report

The generate job writes `ci.env` and exposes it as a GitLab dotenv report, so
later jobs get variables automatically:

```yaml
publish:
  stage: deploy
  image: alpine:3
  script:
    - echo "PNG at $AUTO_ARCH_PNG"
    - test -f "$AUTO_ARCH_MD"
```

Available variables: `AUTO_ARCH_HAS_CHANGES`, `AUTO_ARCH_OUT_DIR`,
`AUTO_ARCH_SUMMARY_FILE`, `AUTO_ARCH_CHANGED_FILES`, `AUTO_ARCH_MD`,
`AUTO_ARCH_MMD`, `AUTO_ARCH_PNG`, `AUTO_ARCH_JPG`, `AUTO_ARCH_SVG`,
`AUTO_ARCH_DRAWIO`, `AUTO_ARCH_HTML`.

Use `needs:` to keep the pipeline fast and download only the diagram artifacts:

```yaml
needs:
  - job: auto-arch-diagram:generate
    artifacts: true
```

### GitLab Pages

```yaml
pages:
  stage: deploy
  needs:
    - job: auto-arch-diagram:generate
      artifacts: true
  script:
    - mkdir -p public
    - cp "$AUTO_ARCH_HTML" public/index.html
    - cp "$AUTO_ARCH_PNG" public/architecture.png
  artifacts:
    paths:
      - public
```

### Committing diagrams back to the repository

GitLab runners cannot push with the implicit job token for protected branches.
Create a project access token with `write_repository` scope, expose it as
`AUTO_ARCH_PUSH_TOKEN`, and add a small follow-up job:

```yaml
commit-diagrams:
  stage: deploy
  needs:
    - job: auto-arch-diagram:generate
      artifacts: true
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script:
    - git config user.name "auto-arch-diagram"
    - git config user.email "auto-arch-diagram@users.noreply.gitlab.com"
    - git add "$AUTO_ARCH_OUT_DIR"
    - git diff --cached --quiet && exit 0
    - git commit -m "chore: update architecture diagrams"
    - git push "https://oauth2:${AUTO_ARCH_PUSH_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git" "HEAD:${CI_COMMIT_BRANCH}"
```

---

## Change detection details

- **Merge request pipelines** diff against `CI_MERGE_REQUEST_DIFF_BASE_SHA`
  (falling back to `git merge-base` with the target branch).
- **Branch pipelines** diff against `CI_COMMIT_BEFORE_SHA`.
- **Scheduled or new-branch pipelines** where no base exists now fall back to a
  full scan instead of silently producing an empty diagram.
- Detect files with `git ls-files` when `force-full` is enabled.
- The template sets `GIT_DEPTH: "0"`; keep it (or fetch the base commit) or
  change detection will fall back to a full scan.

Set `AUTO_ARCH_CHANGED_FILES` (or the `changed-files` input) to override
detection entirely, for example from a scheduler script.

---

## Self-hosted GitLab and air-gapped runners

1. Mirror this repository into your GitLab instance.
2. Vendor the include template (`include: local`) or use the component.
3. Point the tool at the mirror:

```yaml
variables:
  AUTO_ARCH_TOOL_REPOSITORY: https://gitlab.example.com/platform/auto-arch-diagram.git
  AUTO_ARCH_TOOL_REF: v2.1.2
```

For private mirrors, embed a read-only deploy token in the clone URL or configure
a runner-level credential helper. The template uses a plain `git clone`, so any
standard Git credential mechanism works.

---

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| "No IaC changes detected" on an MR | Shallow clone or missing diff base. Keep `GIT_DEPTH: "0"` or set `force-full: true`. |
| `No such file or directory: .auto-arch-diagram-tool` | Tool clone failed. Check runner egress and `tool-repository` / `tool-ref`. |
| `graphviz` not found | The image is not Debian-based, or `install-system-packages` is `false`. Install Graphviz in the image. |
| Merge request note missing | `AUTO_ARCH_GITLAB_TOKEN` not set, lacks `api` scope, or the pipeline is not a merge request pipeline. |
| Job is skipped on feature branches | By default only merge requests, the default branch and manual runs trigger it. Set `always-run: true` / `AUTO_ARCH_ALWAYS_RUN: "true"`. |
| Artifacts are empty | The generation step failed; check earlier log lines. `ci.env` records `AUTO_ARCH_HAS_CHANGES=false` when the change set had no IaC files. |
| AI outputs missing | `ai-enhance` disabled, API key missing, or quota exhausted. Standard outputs remain valid. |

---

## Migrating from the GitHub Actions workflow

| GitHub Actions | GitLab |
| --- | --- |
| `with: direction: AUTO` | `direction: AUTO` (component) / `AUTO_ARCH_DIRECTION: AUTO` |
| `with: comment_on_pr: true` | `mr-comment: true` + `AUTO_ARCH_GITLAB_TOKEN` |
| `with: force_full: true` | `force-full: true` / `AUTO_ARCH_FORCE_FULL: "true"` |
| `secrets: GEMINI_API_KEY` | Masked CI/CD variable `GEMINI_API_KEY` |
| `actions/upload-artifact` | `artifacts:paths` in the job |
| `permissions: pull-requests: write` | Project access token with `api` scope |
| `runner: self-hosted` | `job-tags: ["self-hosted"]` |

The generator and every output format are identical between the two platforms.
