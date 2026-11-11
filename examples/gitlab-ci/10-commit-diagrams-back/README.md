# 10 — Commit diagrams back to the repository

Keeps generated diagrams next to the IaC by committing them from a follow-up job
on the default branch.

## Pipeline

```yaml
include:
  - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@1.0.0
    inputs:
      iac-root: infra
      out-dir: docs/architecture
      image-formats: png,svg
      mr-comment: true

commit-diagrams:
  stage: deploy
  needs:
    - job: auto-arch-diagram
      artifacts: true
  image: alpine:3.20
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_PIPELINE_SOURCE == "web"
  before_script:
    - apk add --no-cache git
  script:
    - git config user.name "auto-arch-diagram"
    - git config user.email "auto-arch-diagram@users.noreply.gitlab.com"
    - git add "$AUTO_ARCH_OUT_DIR"
    - git diff --cached --quiet && exit 0
    - git commit -m "chore: update architecture diagrams [skip ci]"
    - git push "https://oauth2:${AUTO_ARCH_PUSH_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git" "HEAD:${CI_COMMIT_BRANCH}"
```

## Required CI/CD variable

| Variable | Type | Scope | Purpose |
| --- | --- | --- | --- |
| `AUTO_ARCH_PUSH_TOKEN` | Masked, protected | `write_repository` | Push the generated files. |

Create a **project access token** with the `write_repository` scope and the
`Maintainer` role (or a role allowed to push to the protected branch). `CI_JOB_TOKEN`
cannot push to protected branches.

> Keep this token separate from `AUTO_ARCH_GITLAB_TOKEN`. The MR-note token only
> needs `api`; the push token only needs `write_repository`.

## Avoiding infinite pipelines

The commit message ends with `[skip ci]`, so GitLab does not start a new pipeline
for the diagram commit. If your project disables that behaviour, add a rule:

```yaml
  rules:
    - if: '$CI_COMMIT_MESSAGE =~ /^chore: update architecture diagrams/'
      when: never
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

## Protected branches

If the default branch is protected:

1. Allow the project access token's role to push.
2. Or allow the bot user in **Settings → Repository → Protected branches**.
3. Keep the token **protected** so it is only exposed on protected branches.

## What gets committed

With `out-dir: docs/architecture`:

```text
docs/architecture/
├── architecture-diagram.md
├── architecture-diagram.mmd
├── architecture-diagram.png
├── architecture-diagram.svg
├── architecture-diagram.drawio
├── architecture-diagram.html
├── gitlab-ci-summary.md
└── ci.env
```

Add `ci.env` and `gitlab-ci-summary.md` to `.gitignore` if you only want the
diagrams themselves.

## Alternative: merge request instead of a direct push

Replace the `git push` with a branch + MR creation using the GitLab API. The
`AUTO_ARCH_GITLAB_TOKEN` from example 03 can create the MR; the push token still
handles the branch. This avoids direct commits to protected branches and gives
reviewers a diff.

## Related examples

- [04 — Monorepo matrix](../04-monorepo-matrix/)
- [09 — Scheduled full scan](../09-scheduled-full-scan/)
