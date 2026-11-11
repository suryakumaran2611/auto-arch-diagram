# 02 — Every component input

Reference pipeline that sets **all** component inputs explicitly. Use it as a
starting point, then delete the inputs you do not need.

> Replace `platform/auto-arch-diagram` with the GitLab group/project where you
> mirrored this repository, and `1.0.0` with a released tag.

## Pipeline

```yaml
include:
  - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@2.1.3
    inputs:
      job-prefix: auto-arch-diagram
      ...
```

## Input groups

| Group | Inputs |
| --- | --- |
| Job placement | `job-prefix`, `stage`, `image`, `install-system-packages`, `job-tags` |
| Tool checkout | `tool-repository`, `tool-ref` |
| Change detection | `changed-files`, `iac-globs`, `iac-root`, `force-full`, `always-run` |
| Outputs | `out-dir`, `image-formats`, `out-md`, `out-mmd`, `out-png`, `out-jpg`, `out-svg`, `out-drawio`, `out-html`, `artifacts-expire-in` |
| Rendering | `direction`, `render-layout`, `render-bg`, `edge-color`, `edge-penwidth`, `edge-arrowsize`, `fontsize`, `iconsize`, `render-engine` |
| Model shape | `simplified`, `expand-badges`, `no-consolidate` |
| Advanced IaC | `planfile`, `graphfile`, `varfile`, `workspace`, `source`, `annotate` |
| AI refinement | `ai-enhance`, `ai-backend`, `gemini-model`, `openrouter-model`, `ollama-model`, `ai-iterations` |
| Merge request note | `mr-comment` |

## Inputs that need files

These are intentionally empty in the pipeline so it runs out of the box:

| Input | Provide when |
| --- | --- |
| `changed-files` | An upstream job already computed the file list. |
| `planfile` | You generated `terraform show -json`, for example `plan.json`. |
| `graphfile` | You generated `terraform graph > graph.dot`. |
| `varfile` | Your Terraform needs `.tfvars` files. |
| `source` | You want to diagram a different remote repository. |
| `annotate` | You have a numbered-flow YAML file. |

## Behaviour notes

- `image-formats: png,jpg,svg` plus the default `out-drawio`/`out-html` produces
  the complete suite.
- `out-drawio: __disabled__` and `out-html: __disabled__` skip those exports.
- `changed-files` overrides diff detection; leave it empty for normal MR use.
- `force-full: true` scans every tracked IaC file; combine with `always-run` for
  scheduled jobs.
- `mr-comment: false` disables the comment job even if a token exists.
- `simplified`, `expand-badges` and `no-consolidate` are independent booleans.
- `varfile` accepts newlines, spaces, commas or semicolons.

## Expected job graph

```text
auto-arch-diagram        (build)  -> artifacts + ci.env
auto-arch-diagram-comment (build) -> sticky MR note, allow_failure
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

- [03 — Terraform + Gemini MR review](../03-terraform-ai-gemini/)
- [08 — Output formats](../08-output-formats/)
- [11 — Advanced IaC inputs](../11-advanced-iac-inputs/)
- [12 — Layout tuning](../12-layout-tuning/)
