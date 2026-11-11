# 09 — Scheduled full scan

Regenerates the diagram from every tracked IaC file on a schedule, even when no
files changed. Useful for drift detection, nightly documentation, and catching
up after a long-lived branch.

## Pipeline

```yaml
include:
  - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@1.0.0
    inputs:
      iac-root: infra
      out-dir: artifacts/architecture
      image-formats: png,svg,drawio,html
      force-full: true
      always-run: true
      mr-comment: false

# Restrict the generated job to scheduled pipelines only.
auto-arch-diagram:
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

## Why both `force-full` and the rules override

- `force-full: true` ignores diff detection and scans all tracked IaC files.
- `always-run: true` adds a rule for every pipeline; the consumer-side
  `rules:` override narrows the job back to schedules.
- `mr-comment: false` prevents the comment job from being created.

## Create the schedule

1. Open **Build → Pipeline schedules → New schedule**.
2. Description: `Nightly architecture diagram`.
3. Interval pattern: `0 2 * * *` (02:00 every day) or a custom cron.
4. Target branch: your default branch.
5. Timezone: your platform timezone.
6. Save and run once with **Run** to verify.

## Recommended settings

| Setting | Why |
| --- | --- |
| `artifacts-expire-in: 30 days` | Keep enough history for audits. |
| `image-formats: png,svg,drawio,html` | Full suite for documentation. |
| `mr-comment: false` | No MR exists in a scheduled pipeline. |
| Protected/masked variables | Keep AI keys and tokens out of logs. |
| Runner concurrency | Nightly runs can overlap; keep the schedule outside peak hours. |

## Optional: custom file list

If you only want part of the repository in the nightly diagram, set
`changed-files` explicitly instead of relying on the full scan:

```yaml
    inputs:
      changed-files: |
        infra/main.tf
        infra/modules/vpc/main.tf
      force-full: false
```

## Verify the run

- The job log starts with `force_full enabled - scanning every tracked IaC file`.
- `ci.env` contains `AUTO_ARCH_HAS_CHANGES=true`.
- Artifacts include `gitlab-ci-summary.md` with the file count.

## Related examples

- [10 — Commit diagrams back](../10-commit-diagrams-back/)
- [05 — GitLab Pages](../05-gitlab-pages/)
