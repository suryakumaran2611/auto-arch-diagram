# Auto Architecture Diagram User Guide

This comprehensive guide will help you set up and use the Auto Architecture Diagram action to automatically generate and maintain architecture diagrams for your Infrastructure as Code (IaC) projects.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Supported IaC Formats](#supported-iac-formats)
5. [Workflow Modes](#workflow-modes)
6. [PR Creation and Updates](#pr-creation-and-updates)
7. [Customization Options](#customization-options)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)
10. [Best Practices](#best-practices)
11. [Confluence Publishing and Image Replacement](#confluence-publishing-and-image-replacement)

## Overview

The Auto Architecture Diagram action automatically:
- Detects changes in your IaC files
- Generates architecture diagrams in multiple formats (Mermaid, PNG, SVG, JPEG)
- Comments on pull requests with updated diagrams
- Optionally creates pull requests to update diagram files in your repository

### Key Features

- **Multi-format Support**: Terraform, CloudFormation, Bicep, Pulumi, AWS CDK
- **Flexible Output**: Mermaid markdown, rendered images (PNG/SVG/JPEG)
- **AI-Powered**: Optional AI mode for enhanced diagram generation
- **PR Integration**: Automatic commenting and diagram PR creation
- **Highly Configurable**: Extensive customization options

## Quick Start

### 1. Basic Setup

Create `.github/workflows/auto-arch-diagram.yml` in your repository:

```yaml
name: Auto Architecture Diagram

on:
  pull_request:
    types: [opened, synchronize, reopened]
    paths:
      - '**/*.tf'
      - '**/*.tfvars'
      - '**/*.bicep'
      - '**/*.cfn.yaml'
      - '**/*.cfn.yml'
      - '**/template.yaml'
      - '**/template.yml'

jobs:
  comment:
    permissions:
      contents: read
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      mode: static
      direction: LR
      comment_on_pr: true
      create_diagram_pr: false
```

### 2. Enable PR Creation (Optional)

To automatically create PRs that update diagram files:

```yaml
  diagram_pr:
    if: github.event_name == 'pull_request_target'
    permissions:
      contents: write
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      mode: static
      direction: LR
      comment_on_pr: false
      create_diagram_pr: true
      publish_enabled: true
```

### 3. Configure Output Paths

Create `.auto-arch-diagram.yml`:

```yaml
publish:
  enabled: true
  paths:
    md: docs/architecture/architecture-diagram.md
    mmd: docs/architecture/architecture-diagram.mmd
    png: docs/architecture/architecture-diagram.png
    svg: docs/architecture/architecture-diagram.svg
```

## Configuration

### Repository Variables

You can configure the action using GitHub repository variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_ARCH_MODE` | `static` | Generation mode: `static` or `ai` |
| `AUTO_ARCH_MODEL` | `gpt-4o-mini` | AI model (when mode=ai) - **Experimental** |
| `AUTO_ARCH_DIRECTION` | `LR` | Diagram direction: `LR`, `TB`, `RL`, `BT`, `AUTO` |
| `AUTO_ARCH_RENDER_LAYOUT` | `lanes` | Layout: `lanes` or `providers` |
| `AUTO_ARCH_RENDER_BG` | `transparent` | Background: `transparent` or `white` |
| `AUTO_ARCH_CREATE_DIAGRAM_PR` | `false` | Enable automatic diagram PR creation |
| `AUTO_ARCH_FORCE_UPDATE` | `false` | Force diagram updates even without IaC changes |

### Configuration File

Create `.auto-arch-diagram.yml` in your repository root:

```yaml
# Configuration for Auto Architecture Diagram
diagram:
  format: mermaid
  direction: LR  # LR, TB, RL, BT, or AUTO

generator:
  mode: static  # static or ai (requires OPENAI_API_KEY)

render:
  layout: lanes  # lanes or providers
  background: transparent  # transparent or white
  lanes: [Network, Security, Containers, Compute, Data, Storage, Other]

publish:
  enabled: true
  paths:
    md: docs/architecture/auto-arch-diagram.md
    mmd: docs/architecture/auto-arch-diagram.mmd
    png: docs/architecture/auto-arch-diagram.png
    jpg: docs/architecture/auto-arch-diagram.jpg
    svg: docs/architecture/auto-arch-diagram.svg

model:
  provider: openai
  name: gpt-4o-mini

limits:
  max_files: 25
  max_bytes_per_file: 30000
```

## Supported IaC Formats

### Terraform
- `**/*.tf`
- `**/*.tfvars`
- `**/*.hcl`

### AWS CloudFormation
- `**/*.cfn.yaml`
- `**/*.cfn.yml`
- `**/*.cfn.json`
- `**/template.yaml`
- `**/template.yml`

### Azure Bicep
- `**/*.bicep`

### Pulumi
- `**/Pulumi.*.yaml`
- `**/Pulumi.*.yml`
- `**/Pulumi.yaml`
- `**/Pulumi.yml`
- `**/Pulumi.*.json`
- `**/Pulumi.*.ts`
- `**/Pulumi.*.py`

### AWS CDK
- `**/*.cdk.ts`
- `**/*.cdk.py`

## Workflow Modes

### Static Mode (Default)

Uses parsers and libraries to analyze IaC files without external AI services.

**Advantages:**
- No API keys required
- Faster execution
- Consistent results
- Free to use

**Limitations:**
- May miss complex architectural relationships
- Limited understanding of custom modules

### AI Mode (Experimental)

⚠️ **Experimental Feature - Not for Production Use**

Uses OpenAI's models to analyze and generate more intelligent diagrams.

**Requirements:**
- `OPENAI_API_KEY` secret in your repository
- API costs may apply

**Advantages:**
- Better understanding of complex architectures
- Can identify relationships not obvious from static analysis
- More intelligent diagram layouts

**⚠️ Experimental Notice:**
- AI-generated diagrams may contain inaccuracies
- API costs can accumulate quickly
- Not recommended for production environments
- Generated diagrams should be reviewed manually

## PR Creation and Updates

### How PR Creation Works

1. **Trigger**: When a pull request is opened or updated with IaC changes
2. **Analysis**: The action analyzes changed IaC files
3. **Generation**: Creates updated diagrams in configured formats
4. **PR Creation**: Creates/updates a separate PR with diagram files

### PR Creation Configuration

To enable automatic diagram PR creation:

```yaml
jobs:
  diagram_pr:
    if: github.event_name == 'pull_request_target'
    permissions:
      contents: write
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      create_diagram_pr: true
      publish_enabled: true
      diagram_pr_branch_prefix: 'auto-arch-diagram/update'
```

### PR Branch Management

- **Branch Name**: `{diagram_pr_branch_prefix}-{pr_number}`
- **Base Branch**: The target branch of the original PR
- **Commit Message**: "chore: update architecture diagram"
- **Auto-merge**: Can be enabled if desired

## Customization Options

### Diagram Direction

| Direction | Description |
|-----------|-------------|
| `LR` | Left to Right (horizontal) |
| `TB` | Top to Bottom (vertical) |
| `RL` | Right to Left |
| `BT` | Bottom to Top |
| `AUTO` | Intelligent selection based on architecture |

### Render Layouts

#### Lanes Layout (Default)
Organizes components by category lanes:
- Network
- Security  
- Containers
- Compute
- Data
- Storage
- Other

#### Providers Layout
Organizes components by cloud provider or service category.

### Background Options

- **Transparent**: Best for dark themes and overlay use
- **White**: Best for print and light themes

### Image Formats

| Format | Best For | Notes |
|--------|----------|-------|
| PNG | General use, good compression | Lossless compression |
| JPEG | Small file size | Lossy compression, not for diagrams with text |
| SVG | Scalable, web use | Vector format, infinite scaling |

## Troubleshooting

### Common Issues

#### 1. "No IaC files found" Error
**Cause**: No files matching the IaC patterns were found.

**Solution**: 
- Check that your files match the supported patterns
- Verify the files are committed to the repository
- Check the `iac_globs` input in your workflow

#### 2. "publish.paths is empty" Error
**Cause**: Missing or incorrect `.auto-arch-diagram.yml` configuration.

**Solution**:
```yaml
publish:
  enabled: true
  paths:
    md: docs/architecture/auto-arch-diagram.md
    mmd: docs/architecture/auto-arch-diagram.mmd
    png: docs/architecture/auto-arch-diagram.png
```

#### 3. PR Not Created
**Cause**: Missing permissions or incorrect event trigger.

**Solution**:
- Ensure `contents: write` and `pull-requests: write` permissions
- Use `pull_request_target` event for PR creation
- Set `create_diagram_pr: true`

#### 4. AI Mode Not Working
**Cause**: Missing or invalid `OPENAI_API_KEY`.

**Solution**:
- Add `OPENAI_API_KEY` as a repository secret
- Verify the API key has sufficient credits
- Check that the model name is correct

### Debug Mode

Add this step to your workflow for debugging:

```yaml
- name: Debug workflow
  run: |
    echo "Event: ${{ github.event_name }}"
    echo "Base ref: ${{ github.event.pull_request.base.ref }}"
    echo "Head ref: ${{ github.event.pull_request.head.ref }}"
    echo "Repository: ${{ github.repository }}"
```

## Advanced Usage

### Custom IaC Patterns

Override the default file patterns:

```yaml
uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
with:
  iac_globs: |
    infra/**/*.tf
    cloudformation/**/*.yaml
    custom/**/*.bicep
```

### Multiple Workflow Files

You can use multiple workflow files for different purposes:

```yaml
# .github/workflows/pr-comments.yml
on:
  pull_request:
    paths: ['**/*.tf']
jobs:
  comment:
    permissions:
      contents: read
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      comment_on_pr: true
      create_diagram_pr: false

---

# .github/workflows/diagram-updates.yml
on:
  pull_request_target:
    paths: ['**/*.tf']
jobs:
  diagram_pr:
    permissions:
      contents: write
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      comment_on_pr: false
      create_diagram_pr: true
```

### Conditional PR Creation

Control PR creation based on file changes:

```yaml
env:
  CREATE_DIAGRAM_PR: ${{ contains(github.event.pull_request.changed_files, 'production/') }}
```

## Best Practices

### 1. Repository Organization

```
your-repo/
├── .github/
│   ├── workflows/
│   │   └── auto-arch-diagram.yml
│   └── auto-arch-diagram.yml
├── docs/
│   └── architecture/
│       ├── architecture-diagram.md
│       ├── architecture-diagram.mmd
│       ├── architecture-diagram.png
│       └── architecture-diagram.svg
└── infrastructure/
    ├── terraform/
    ├── cloudformation/
    └── bicep/
```

### 2. Branch Strategy

- **Main Branch**: Always has up-to-date diagrams
- **Feature Branches**: PR comments show diagram changes
- **Release Branches**: Automatic diagram updates via PR creation

### 3. Performance Optimization

- Use `force_full: false` for large repositories
- Limit file analysis with custom `iac_globs`
- Cache dependencies in workflows

### 4. Security Considerations

- Never commit API keys to your repository
- Use repository secrets for sensitive data
- Review generated diagrams for sensitive information
- Use `pull_request_target` for untrusted forks
- **AI Mode**: OpenAI API keys transmit your IaC code to external services
- **AI Mode**: Review your organization's data sharing policies before use
- **AI Mode**: Consider the implications of sending infrastructure code to third parties

### 5. Integration with Documentation

- Include diagrams in your documentation site
- Use GitHub Pages to host generated diagrams
- Link to diagrams from README files
- Update diagrams as part of your release process

## Confluence Publishing and Image Replacement

The Auto Architecture Diagram action supports robust publishing and replacement of diagrams in Confluence pages. You can target a specific image using a unique marker or filename, ensuring only the intended diagram is updated.

### Example Workflow

```yaml
with:
  direction: AUTO
  image_formats: png,svg
  publish_enabled: true
  publish_confluence: true
  confluence_url: ${{ secrets.CONFLUENCE_URL }}
  confluence_user: ${{ secrets.CONFLUENCE_USER }}
  confluence_token: ${{ secrets.CONFLUENCE_TOKEN }}
  confluence_page_id: '123456789'  # Target Confluence page ID
  confluence_replace: true         # Replace existing diagram on the page
  confluence_image_marker: '<!-- auto-arch-diagram:architecture-diagram.png -->' # Unique marker for image replacement
```

### How It Works
- The workflow searches for the marker or filename in the Confluence page and replaces only that image.
- If the marker is not found, it falls back to replacing the first image or prepends the new image.
- Use a unique marker for each diagram to avoid accidental replacement of other images.

### Best Practices
- Use a unique marker for each diagram type or environment (e.g., `<!-- auto-arch-diagram:prod.png -->`).
- Store Confluence credentials as repository secrets.
- Test the workflow with a test page before using in production.
- Review the page source in Confluence to confirm marker placement.

### Troubleshooting
- If the image is not replaced, check that the marker matches exactly in the page source.
- Ensure the page ID and credentials are correct.
- Review workflow logs for error messages from the Confluence API.
- If multiple diagrams are present, use distinct markers for each.

### Required Secrets
- `CONFLUENCE_URL`: Base URL of your Confluence instance (e.g., `https://your-domain.atlassian.net/wiki`)
- `CONFLUENCE_USER`: Confluence username or email
- `CONFLUENCE_TOKEN`: API token generated from Confluence

### Environment Variables
- `CONFLUENCE_IMAGE_MARKER`: (Optional) Unique marker to target a specific image for replacement.

### Advanced Example: Multiple Diagrams

```yaml
with:
  direction: AUTO
  image_formats: png,svg
  publish_enabled: true
  publish_confluence: true
  confluence_url: ${{ secrets.CONFLUENCE_URL }}
  confluence_user: ${{ secrets.CONFLUENCE_USER }}
  confluence_token: ${{ secrets.CONFLUENCE_TOKEN }}
  confluence_page_id: '123456789'
  confluence_replace: true
  confluence_image_marker: '<!-- auto-arch-diagram:staging-architecture.png -->'
```

**Tip:** Use different markers for staging, production, or environment-specific diagrams.

### Security & Best Practices
- Never commit API tokens to your repository.
- Use repository secrets for all sensitive data.
- Review generated diagrams for sensitive information before publishing.
- Use a test page for initial integration to avoid overwriting important documentation.

### FAQ
- **Q: Can I replace multiple images in one page?**
  - Yes, by running the workflow multiple times with different markers and filenames.
- **Q: What if the marker is missing?**
  - The workflow will replace the first image or prepend the new image to the page.
- **Q: How do I debug Confluence publishing issues?**
  - Check workflow logs for API errors, verify credentials, and confirm marker placement in the page source.

For more examples and advanced usage, see the README and workflow documentation.

## Example Implementations

### Basic Terraform Repository

```yaml
# .github/workflows/diagrams.yml
name: Architecture Diagrams

on:
  pull_request:
    paths: ['terraform/**/*.tf']

jobs:
  diagrams:
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      mode: static
      direction: TB
      comment_on_pr: true
    secrets:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Multi-Cloud Setup

```yaml
# .auto-arch-diagram.yml
diagram:
  direction: AUTO

generator:
  mode: ai

render:
  layout: providers
  background: transparent

publish:
  enabled: true
  paths:
    md: docs/diagrams/multi-cloud-architecture.md
    mmd: docs/diagrams/multi-cloud-architecture.mmd
    svg: docs/diagrams/multi-cloud-architecture.svg
```

### Enterprise Configuration

```yaml
# .github/workflows/enterprise-diagrams.yml
name: Enterprise Architecture Diagrams

on:
  pull_request:
    paths:
      - '**/*.tf'
      - '**/*.bicep'
      - '**/*.yaml'

jobs:
  comment:
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      mode: ai
      direction: AUTO
      render_layout: lanes
      comment_on_pr: true
      create_diagram_pr: false
      image_formats: png,svg
      force_full: false
    secrets:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

  update-diagrams:
    if: github.event_name == 'pull_request_target'
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      mode: ai
      direction: AUTO
      comment_on_pr: false
      create_diagram_pr: true
      publish_enabled: true
    secrets:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Force Updates

Sometimes you may want to regenerate architecture diagrams even when no IaC files have changed. This is useful for:
- Updating diagram styling or configuration changes
- Testing workflow modifications
- Updating icons or rendering engine improvements
- Migrating between different diagram layouts

### Manual Force Update

You can manually trigger a workflow with the force update option:

1. Go to the **Actions** tab in your repository
2. Select the **Auto Architecture Diagram** workflow
3. Click **Run workflow**
4. Check **Force architecture diagram update even if no IaC files changed**
5. Click **Run workflow**

### Automatic Force Updates

Set the `AUTO_ARCH_FORCE_UPDATE` repository variable to `true` to force updates on every push to main/develop branches:

```yaml
# Repository Settings → Variables → New repository variable
Name: AUTO_ARCH_FORCE_UPDATE
Value: true
```

### Force Update in Workflow Configuration

```yaml
jobs:
  comment:
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@main
    with:
      force_full: true  # Force diagram generation regardless of file changes
```

## Upcoming Features

The following features are planned for future releases:

### 🤖 Enhanced AI Capabilities
- **Multiple AI Providers**: Support for Claude, Gemini, and local AI models
- **Advanced Analysis**: Better understanding of complex architectural patterns
- **Custom Prompts**: User-defined AI prompts for specialized diagram generation
- **Smart Layouts**: AI-driven layout optimization based on diagram complexity

### 🔌 Integration Expansions
- **Confluence Integration**: Automatic diagram publishing to Confluence pages
- **Notion Integration**: Direct updates to Notion databases and pages
- **Slack/Discord**: Diagram sharing and notifications in team channels
- **Jira Integration**: Link diagrams to Jira tickets and documentation

### 📊 Advanced Features
- **Cost Estimation**: Integration with cloud pricing APIs for cost-aware diagrams
- **Security Insights**: Automated security recommendations in diagrams
- **Compliance Checking**: Compliance overlays and certifications display
- **Version Comparison**: Visual diff between diagram versions

### 🎨 Enhanced Customization
- **Custom Themes**: User-defined color schemes and styles
- **Branding Options**: Company logos and custom branding in diagrams
- **Interactive Diagrams**: Clickable components with drill-down capabilities
- **Diagram Templates**: Pre-built templates for common architectures

### 🔧 Developer Experience
- **Local CLI**: Command-line interface for local diagram generation
- **IDE Extensions**: VS Code and JetBrains IDE integrations
- **API Access**: REST API for programmatic diagram generation
- **Webhooks**: Custom webhooks for diagram generation events

## Experimental Features

The following features are currently experimental and not recommended for production use:

### 🧠 AI-Generated Diagrams
- **Status**: Experimental
- **Warning**: May contain inaccuracies and security implications
- **Use Case**: Testing and evaluation only
- **Future Plans**: Production-ready with multiple provider support

### 🔗 Third-Party Integrations
- **Status**: Planned
- **Warning**: Not yet implemented
- **Use Case**: Future roadmap items
- **Timeline**: Q2 2025 onwards

## Getting Help

If you encounter issues:

1. **Check the logs**: Review the workflow run logs for error messages
2. **Verify configuration**: Ensure all required files and secrets are in place
3. **Test with static mode**: Try static mode first to isolate AI-related issues
4. **Check file patterns**: Verify your IaC files match the supported patterns
5. **Review permissions**: Ensure proper GitHub token permissions
6. **Force update**: Try a force update if diagrams seem outdated

For additional support:
- Create an issue in the [Auto Architecture Diagram repository](https://github.com/suryakumaran2611/auto-arch-diagram)
- Check the [GitHub discussions](https://github.com/suryakumaran2611/auto-arch-diagram/discussions)
- Review existing [issues and solutions](https://github.com/suryakumaran2611/auto-arch-diagram/issues)
- **AI Mode Issues**: Report AI-specific issues with detailed logs and examples

---

**Note on Experimental Features**: Features marked as experimental are provided for testing and evaluation purposes only. They should not be used in production environments and may change significantly in future releases.

---

This documentation is maintained as part of the Auto Architecture Diagram project. For the latest updates and examples, visit the [project repository](https://github.com/suryakumaran2611/auto-arch-diagram).