# 04 — Monorepo matrix

Generates one independent diagram per Terraform module by including the
component once per module with a unique `job-prefix` and output folder.

## Pipeline

```yaml
include:
  - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@1.0.0
    inputs:
      job-prefix: network-diagram
      iac-root: infra/network
      out-dir: artifacts/network
      mr-comment: false

  - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@1.0.0
    inputs:
      job-prefix: data-diagram
      iac-root: infra/data
      out-dir: artifacts/data
      mr-comment: false
```

## How change detection works per module

The shared runner filters changed files to the module root before calling the
generator. A change to `infra/network/vpc.tf` therefore only regenerates the
network diagram; a change in `infra/data` only regenerates the data diagram. If
both modules change, both jobs run in parallel.

## Why `mr-comment: false`

Every comment job updates the same sticky note marker
(`<!-- auto-arch-diagram -->`). Running several comment jobs would make them
overwrite each other. Enable it on exactly one module:

```yaml
      mr-comment: true   # on network-diagram only
```

Alternatively, keep comments disabled and publish artifacts/Pages instead.

## Expected jobs

```text
network-diagram          -> artifacts/network/
network-diagram-comment  -> skipped (mr-comment false)
data-diagram             -> artifacts/data/
data-diagram-comment     -> skipped (mr-comment false)
```

## Add more modules

Copy an include block and change three values:

```yaml
      job-prefix: observability-diagram
      iac-root: infra/observability
      out-dir: artifacts/observability
```

Keep `job-prefix` unique: it is the GitLab job name and must not collide.

## Consuming all module outputs

```yaml
summary:
  stage: deploy
  needs:
    - job: network-diagram
      artifacts: true
    - job: data-diagram
      artifacts: true
  script:
    - find artifacts -name 'ci.env' -print
```

## Related examples

- [05 — GitLab Pages](../05-gitlab-pages/)
- [10 — Commit diagrams back](../10-commit-diagrams-back/)
