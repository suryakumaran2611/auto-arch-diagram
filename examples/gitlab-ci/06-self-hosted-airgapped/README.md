# 06 — Self-hosted / air-gapped

Runs the pipeline entirely inside your network: vendored template, mirrored tool
repository, a pre-baked runner image and tagged runners.

## Pipeline

```yaml
include:
  - local: ci/gitlab/auto-arch-diagram.gitlab-ci.yml

variables:
  AUTO_ARCH_TOOL_REPOSITORY: https://gitlab.example.com/platform/auto-arch-diagram.git
  AUTO_ARCH_TOOL_REF: v2.1.3
  AUTO_ARCH_IMAGE: registry.example.com/platform/python:3.12-graphviz
  AUTO_ARCH_INSTALL_SYSTEM_PACKAGES: "false"
  AUTO_ARCH_IAC_ROOT: terraform
  AUTO_ARCH_OUT_DIR: artifacts/architecture

auto-arch-diagram:generate:
  tags: [self-hosted, docker]
auto-arch-diagram:comment:
  tags: [self-hosted, docker]
```

## Step-by-step setup

1. **Mirror this repository** into your GitLab group and push a tag:

   ```bash
   git clone --mirror https://github.com/suryakumaran2611/auto-arch-diagram.git
   cd auto-arch-diagram.git
   git push --mirror https://gitlab.example.com/platform/auto-arch-diagram.git
   ```

2. **Vendor the template** into your project so pipeline changes are reviewed
   like application code:

   ```bash
   mkdir -p ci/gitlab
   cp /path/to/auto-arch-diagram/ci/gitlab/auto-arch-diagram.gitlab-ci.yml ci/gitlab/
   ```

   Or use the component instead:

   ```yaml
   include:
     - component: $CI_SERVER_FQDN/platform/auto-arch-diagram/auto-arch-diagram@2.1.3
       inputs:
         tool-repository: https://gitlab.example.com/platform/auto-arch-diagram.git
         tool-ref: v2.1.3
         job-tags: [self-hosted, docker]
   ```

3. **Build a pre-baked image** containing Python dependencies and Graphviz, so
   the job does not need `apt-get` or PyPI at runtime:

   ```dockerfile
   FROM python:3.12-slim
   RUN apt-get update \
    && apt-get install -y --no-install-recommends graphviz fonts-open-sans git \
    && rm -rf /var/lib/apt/lists/*
   COPY requirements.txt /tmp/requirements.txt
   RUN pip install --no-cache-dir -r /tmp/requirements.txt
   ```

4. **Point the template at the image** with `AUTO_ARCH_IMAGE` and set
   `AUTO_ARCH_INSTALL_SYSTEM_PACKAGES: "false"`.

5. **Add runner tags** to both jobs. The include template lets you override any
   job key by redefining the job name.

## Private tool repository

The template performs a plain `git clone`. Use one of:

- A read-only deploy token embedded in the URL:
  `https://deploy-token:${AUTO_ARCH_DEPLOY_TOKEN}@gitlab.example.com/...`
- A runner-level credential helper.
- A pre-cloned tool checkout mounted into the image, with
  `AUTO_ARCH_TOOL_DIR` pointed at it (the template clones only when the directory
  is absent).

## Air-gapped checklist

- [ ] Tool repository mirrored and reachable from the runner.
- [ ] Container image pre-baked with Graphviz, fonts and Python dependencies.
- [ ] `AUTO_ARCH_INSTALL_SYSTEM_PACKAGES: "false"`.
- [ ] PyPI either mirrored or baked into the image.
- [ ] `AUTO_ARCH_TOOL_REF` pinned to a tag or SHA, never `main`.
- [ ] Runner tags match your fleet.
- [ ] Optional: AI backends need egress to Google/OpenRouter, or use `ollama`
      with a local model.

## Using a private GitLab container registry

```yaml
variables:
  AUTO_ARCH_IMAGE: $CI_REGISTRY/platform/python:3.12-graphviz
  DOCKER_AUTH_CONFIG: '{"auths":{...}}'
```

`DOCKER_AUTH_CONFIG` is a masked variable used by the runner to pull private
images.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `git clone` hangs | Runner cannot reach the mirrored repository. Check egress and DNS. |
| `graphviz` not found | Set `AUTO_ARCH_INSTALL_SYSTEM_PACKAGES: "true"` or bake Graphviz into the image. |
| `pip install` fails offline | Pre-install dependencies in the image or configure an internal index. |
| Jobs queued forever | `tags:` do not match any online runner. |

See the [full GitLab guide](../../../docs/GITLAB_CI.md#self-hosted-gitlab-and-air-gapped-runners)
for additional details.

## Which version should I use?

This example pins `AUTO_ARCH_TOOL_REF` to the current release (`v2.1.3`). If you
are not sure which version to use, point it at the `main` branch of your mirror:

```yaml
variables:
  AUTO_ARCH_TOOL_REF: main
```

`main` tracks the latest code without needing a release tag on the mirror, which
is handy while you are evaluating the tool. It is not reproducible, so pin a tag
or commit SHA before relying on it in production.
