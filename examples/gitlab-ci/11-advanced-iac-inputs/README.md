# 11 — Advanced IaC inputs

Covers pre-generated Terraform plans and graphs, variable files, workspaces,
numbered-flow annotations and diagramming a remote repository.

This example assumes these paths exist in the job workspace (committed or
produced by earlier jobs):

| Path | Produced by |
| --- | --- |
| `plan.json` | `terraform show -json plan.tfplan > plan.json` |
| `graph.dot` | `terraform graph > graph.dot` |
| `environments/prod/common.tfvars` | Your repository |
| `environments/prod/network.tfvars` | Your repository |
| `docs/flows.yaml` | Your annotation file |

If a file is missing, that job fails while the others continue.

## Variants

### A. Pre-generated plan

```yaml
      job-prefix: diagram-planfile
      planfile: plan.json
      out-dir: artifacts/plan
```

`planfile` skips HCL parsing and builds the diagram from the plan JSON. Generate
it in an earlier job and pass it as an artifact:

```yaml
prepare-plan:
  stage: prepare
  image: hashicorp/terraform:1.9
  script:
    - cd infra
    - terraform init
    - terraform plan -out=plan.tfplan
    - terraform show -json plan.tfplan > ../plan.json
  artifacts:
    paths: [plan.json]

include:
  - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@1.0.0
    inputs:
      planfile: plan.json
      stage: build
```

### B. Pre-generated graph

```yaml
      job-prefix: diagram-graphfile
      graphfile: graph.dot
      out-dir: artifacts/graph
```

`graphfile` uses `terraform graph` DOT output. It is fast and captures
dependencies, but the plan JSON carries richer resource attributes.

### C. Variable files and workspace

```yaml
      job-prefix: diagram-varfiles
      iac-root: infra
      varfile: |
        environments/prod/common.tfvars
        environments/prod/network.tfvars
      workspace: prod
      annotate: docs/flows.yaml
      out-dir: artifacts/annotated
```

`varfile` accepts newlines, spaces, commas or semicolons; each entry becomes a
separate `--varfile` flag. `workspace` selects the Terraform workspace used when
reading variables.

### D. Remote repository

```yaml
      job-prefix: diagram-remote-source
      source: https://gitlab.example.com/platform/landing-zone.git//terraform
      out-dir: artifacts/remote
```

`source` clones the repository during generation and auto-discovers its `.tf`
files. Change detection is skipped for that run; `iac-root` and `changed-files`
do not apply. For private repositories, embed a read-only deploy token in the URL
or configure a runner credential helper.

## Precedence rules

- `planfile` and `graphfile` take precedence over HCL parsing.
- `source` overrides the checked-out project; `iac-root` is ignored.
- `changed-files` overrides diff detection only when `source` is empty.
- `force-full` scans every tracked file in the current project.
- `annotate` is applied after the inventory is built, regardless of source.

## Numbered flow annotations

`docs/flows.yaml` maps numbered steps to edges, for example:

```yaml
flows:
  - step: 1
    label: "User request"
    from: aws_lb.public
    to: aws_ecs_service.api
  - step: 2
    label: "Read model"
    from: aws_ecs_service.api
    to: aws_dynamodb_table.orders
```

See the full input reference in
[`docs/GITLAB_CI.md`](../../../docs/GITLAB_CI.md#component-inputs) and the
[layout example](../12-layout-tuning/).

## Related examples

- [09 — Scheduled full scan](../09-scheduled-full-scan/)
- [12 — Layout tuning](../12-layout-tuning/)
- [GitLab guide: advanced inputs](../../../docs/GITLAB_CI.md#advanced-iac-and-layout-inputs)
