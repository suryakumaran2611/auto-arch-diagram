# 05 — GitLab Pages

Publishes the interactive HTML studio and the static diagrams to GitLab Pages so
reviewers can browse them without downloading pipeline artifacts.

## Pipeline

```yaml
include:
  - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@2.1.3
    inputs:
      iac-root: infra
      out-dir: artifacts/architecture
      image-formats: png,svg
      mr-comment: true

pages:
  stage: deploy
  needs:
    - job: auto-arch-diagram
      artifacts: true
  script:
    - mkdir -p public
    - cp "$AUTO_ARCH_HTML" public/index.html
    - cp "$AUTO_ARCH_PNG" public/architecture.png
    - cp "$AUTO_ARCH_SVG" public/architecture.svg
  artifacts:
    paths:
      - public
```

## What gets published

| File | Source |
| --- | --- |
| `public/index.html` | `AUTO_ARCH_HTML` — pan/zoom studio, search, resource drawer |
| `public/architecture.png` | `AUTO_ARCH_PNG` |
| `public/architecture.svg` | `AUTO_ARCH_SVG` |

Add `AUTO_ARCH_DRAWIO` if you want the editable draw.io file available too:

```yaml
    - cp "$AUTO_ARCH_DRAWIO" public/architecture.drawio
```

## How the variables arrive

The generate job exports `ci.env` as a dotenv report. The `needs` entry downloads
the artifacts and makes `AUTO_ARCH_HTML`, `AUTO_ARCH_PNG`, `AUTO_ARCH_SVG`,
`AUTO_ARCH_DRAWIO`, and friends available to the Pages job.

## Enabling Pages

1. Go to **Deploy → Pages** in the project.
2. Ensure Pages is enabled and note the generated URL
   (`https://<namespace>.gitlab.io/<project>/`).
3. Run a pipeline on the default branch.

## Rules

The Pages job only runs on the default branch or a manual pipeline. Merge request
pipelines still generate diagrams and the sticky note, but do not publish Pages.

## Custom domains and access control

Configure a custom domain or make Pages private in **Deploy → Pages → Settings**.
The published HTML is fully self-contained and works offline once downloaded.

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

- [04 — Monorepo matrix](../04-monorepo-matrix/)
- [10 — Commit diagrams back](../10-commit-diagrams-back/)
