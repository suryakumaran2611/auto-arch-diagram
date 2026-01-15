# auto-arch-diagram

[![Python Tests](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/python-tests.yml/badge.svg)](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/python-tests.yml)
[![Secret Scan](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/secret-scan.yml)

🏗️ **Professional architecture diagram generation from Infrastructure-as-Code** - Automatically visualize AWS, Azure, GCP, IBM, and Oracle Cloud architectures with best-practice styling and VPC/network grouping.

## ✨ Key Features

- 🎯 **VPC/Network Grouping**: Resources automatically organized within VPCs with public/private subnet distinction
- 🎨 **Professional Styling**: Semi-transparent clusters, intelligent edge types (dashed security, bold data, dotted dependencies)
- 🧠 **AUTO Layout**: 6-factor intelligent analysis chooses optimal horizontal/vertical orientation
- 📊 **Dynamic Spacing**: Self-adjusting layout based on complexity (nodes, edges, nesting depth)
- 🏗️ **Multi-Cloud**: 2,100+ official icons for AWS, Azure, GCP, IBM Cloud, Oracle Cloud
- 📤 **Multiple Formats**: Mermaid (inline), PNG, SVG, JPEG with embedded base64 icons
- 🚀 **Fast & Efficient**: Intelligent overlap prevention and edge routing
- 🔒 **Security-First**: Secret scanning, minimal permissions, safe PR handling

## 🎯 Quick Start

### Using Reusable Workflow (Recommended)

Create `.github/workflows/auto-arch-diagram.yml` in your repository:

```yaml
name: Architecture Diagram

on:
  pull_request:
    paths:
      - 'terraform/**/*.tf'
      - '**/*.bicep'
      - '**/template.yaml'

jobs:
  diagram:
    permissions:
      contents: read
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
    with:
      direction: AUTO                 # Intelligent layout
      image_formats: png,svg
      comment_on_pr: true
```

### Common Configuration Patterns

**Multi-Cloud with Custom Paths**
```yaml
with:
  direction: AUTO
  image_formats: png,svg
  iac_globs: |
    infrastructure/terraform/**/*.tf
    cloudformation/**/*.yaml
  out_md: docs/architecture/diagram.md
  out_png: docs/architecture/diagram.png
  out_svg: docs/architecture/diagram.svg
```

**Mermaid-Only (Fastest)**
```yaml
with:
  mode: static
  image_formats: none
  out_dir: artifacts
```

**Force Full Architecture (Ignore Changes)**
```yaml
with:
  direction: AUTO
  force_full: true
  image_formats: png,svg,jpg
```

**With Diagram Commit PR**
```yaml
on:
  pull_request_target:
    types: [opened, synchronize, reopened]

jobs:
  diagram_pr:
    permissions:
      contents: write
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
    with:
      direction: AUTO
      image_formats: png,svg
      publish_enabled: true          # Commits to publish.paths in .auto-arch-diagram.yml
      create_diagram_pr: true
```

## 📋 Configuration Reference

### Workflow Inputs

| Parameter | Default | Description |
|-----------|---------|-------------|
| `direction` | `LR` | `AUTO` (intelligent), `LR` (→), `TB` (↓), `RL` (←), `BT` (↑) |
| `mode` | `static` | `static` (no AI) or `ai` (requires OPENAI_API_KEY) |
| `model` | `gpt-4o-mini` | AI model when mode=ai |
| `render_layout` | `lanes` | `lanes` (category-first) or `providers` (cloud-first) |
| `render_bg` | `transparent` | PNG/SVG background: `transparent` or `white` |
| `image_formats` | `png,jpg,svg` | Formats to generate (comma-separated) or `none` |
| `iac_globs` | (multiple) | Glob patterns for IaC file detection |
| `out_dir` | `artifacts` | Output directory for generated files |
| `out_md` | `''` | Override markdown output path |
| `out_mmd` | `''` | Override Mermaid output path |
| `out_png` | `''` | Override PNG output path |
| `out_jpg` | `''` | Override JPEG output path |
| `out_svg` | `''` | Override SVG output path |
| `comment_on_pr` | `true` | Post/update sticky PR comment |
| `publish_enabled` | `false` | Write to paths in `.auto-arch-diagram.yml` |
| `create_diagram_pr` | `false` | Create diagram update PR (needs contents:write) |
| `force_full` | `false` | Render full architecture (ignore change detection) |

### Advanced Configuration (`.auto-arch-diagram.yml`)

```yaml
# Generator mode
generator:
  mode: static  # static | ai

# AI model (when mode=ai)
model:
  name: gpt-4o-mini

# File limits
limits:
  max_files: 25
  max_bytes_per_file: 30000

# Output publishing (for diagram PRs)
publish:
  enabled: true
  paths:
    md: docs/architecture/diagram.md
    mmd: docs/architecture/diagram.mmd
    png: docs/architecture/diagram.png
    jpg: docs/architecture/diagram.jpg
    svg: docs/architecture/diagram.svg

# Rendering configuration
render:
  layout: lanes          # lanes | providers
  
  # Layout orientation - AUTO for intelligent selection
  # direction: AUTO is set via workflow input
  
  # Category lanes (used when layout=lanes)
  lanes:
    - Network
    - Security
    - Containers
    - Compute
    - Data
    - Storage
    - Other
  
  # Spacing configuration
  graph:
    pad: auto            # auto | numeric (0.0-2.0)
    nodesep: auto        # auto | numeric (0.0-2.0)
    ranksep: auto        # auto | numeric (0.0-3.0)
    
    # Auto-spacing constraints
    min_pad: 0.4
    min_nodesep: 0.6
    min_ranksep: 0.9
    complexity_scale: 1.5
    edge_density_scale: 1.2
    
    # Edge routing and styling
    edge_routing: ortho         # ortho | spline | polyline | curved
    overlap_removal: prism      # prism | scalexy | compress | vpsc | false
    splines: ortho
    concentrate: false
  
  # Styling
  background: transparent       # transparent | white
  fontname: Helvetica
  graph_fontsize: 18
  
  # Node configuration
  node:
    fontsize: 9
    width: 0.85
    height: 0.85
  
  # Edge configuration
  edge_color: "#6B7280"
  edge_penwidth: 0.9
  edge_arrowsize: 0.65
```

## 🎨 Architecture Best Practices

### VPC/Network Grouping

Resources are automatically organized within their VPC/VNet/VCN containers:

- **VPC Clusters**: Automatically detect and group VPC/VNet/VCN resources
- **Subnet Grouping**: Public subnets (dashed border) vs Private subnets (solid border)
- **Resource Placement**: EC2, Lambda, RDS automatically placed in correct subnet
- **Color Coding**: Semi-transparent colors (AWS orange, Azure blue, GCP green)

### Intelligent Edge Styling

Connections use different styles based on relationship type:

- **Solid Lines**: Network connections (default)
- **Dashed Lines**: Security groups, firewalls, IAM policies (red)
- **Bold Lines**: Data flow connections to databases/storage (blue)
- **Dotted Lines**: Cross-cloud/cross-region dependencies (gray)

### AUTO Direction Selection

The `AUTO` mode uses 6-factor scoring to choose optimal orientation:

**Horizontal (LR) favored when:**
- Wide architectures (4+ lanes, 3+ providers)
- Large diagrams (50+ resources)
- Many small clusters
- Low edge density (<2.0 edges/node)

**Vertical (TB) favored when:**
- Deep nesting (3+ levels)
- High edge density (>3.0 edges/node)
- Few large clusters
- Provider-first layout

**Debug output:**
```yaml
env:
  AUTO_ARCH_DEBUG: "1"  # Shows scoring details
```

## 🏗️ Supported IaC Types

| Type | Extensions | Support Level |
|------|------------|---------------|
| **Terraform** | `*.tf`, `*.tfvars`, `*.hcl` | ✅ Full (VPC grouping, 50+ AWS icons) |
| **CloudFormation** | `template.yaml`, `*.cfn.*` | ✅ Full (Ref, GetAtt, Sub, DependsOn) |
| **Bicep** | `*.bicep` | ✅ Good (resource, dependsOn, parent) |
| **Pulumi YAML** | `Pulumi.yaml` | ✅ Good (resources, dependsOn) |
| **Pulumi TS/Py** | `Pulumi.*.ts`, `Pulumi.*.py` | ⚠️ Limited (requires AI mode) |
| **CDK** | `*.cdk.ts`, `*.cdk.py` | ⚠️ Limited (requires AI mode) |

## 📊 Example Outputs

### Complex Serverless Data Pipeline (Custom Icons)

[examples/terraform/custom-icons-demo/architecture-diagram.png](examples/terraform/custom-icons-demo/architecture-diagram.png)

**Demonstrates:**
- **Custom Icon Support**: 11 custom icons for specialized components (DataPipeline, StreamProcessor, SearchEngine, etc.)
- **Event-Driven Architecture**: API Gateway → Lambda → Kinesis → ElasticSearch workflow
- **VPC Grouping**: Resources organized within VPC with public/private subnet distinction
- **Multiple Data Stores**: S3, DynamoDB, ElasticSearch, Glue Catalog integration
- **Serverless Patterns**: Lambda functions, Step Functions, EventBridge, SNS/SQS
- **Professional Styling**: White backgrounds, colored borders, center-based edge routing
- **Complex Topology**: 40+ resources with intelligent AUTO layout selection

**Key Features Showcased:**
- Custom icon integration (Icon tag support)
- Real-time streaming (Kinesis + Lambda)
- Batch processing (S3 events + Glue Crawler)
- Search/analytics (ElasticSearch + Athena)
- Monitoring/alerts (CloudWatch + SNS)
- Dead letter queue handling

### All Examples

Explore [examples/terraform/](examples/terraform/) for:
- **custom-icons-demo**: Serverless data pipeline with 11 custom icons (40+ resources)
- **serverless-website**: Multi-cloud serverless architectures (AWS, Azure, GCP, IBM, OCI)

## 🚀 Local Development

### Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For AI mode
pip install -r requirements-ai.txt
```

### Generate Diagram

```bash
# Basic usage
python tools/generate_arch_diagram.py \
  --changed-files "terraform/main.tf terraform/vpc.tf" \
  --direction AUTO \
  --out-md artifacts/diagram.md \
  --out-png artifacts/diagram.png \
  --out-svg artifacts/diagram.svg

# With debug output
export AUTO_ARCH_DEBUG=1
python tools/generate_arch_diagram.py \
  --changed-files "terraform/**/*.tf" \
  --direction AUTO \
  --out-png diagram.png

# AI mode
export AUTO_ARCH_MODE=ai
export OPENAI_API_KEY=sk-...
python tools/generate_arch_diagram.py \
  --changed-files "cdk/app.ts" \
  --direction AUTO \
  --out-png diagram.png
```

### Regenerate Examples

```bash
# Regenerate all example diagrams
python tools/regenerate_examples.py

# With custom config
export AUTO_ARCH_PUBLISH_ENABLED=false
python tools/regenerate_examples.py
```

### Run Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_static_terraform.py

# Run with coverage
pytest --cov=tools --cov-report=html
```

## 🔒 Security Features

### Secret Scanning
- **gitleaks**: Scans for hardcoded secrets
- **Redaction**: Automatic redaction of `password=`, `token:` patterns
- **Truncation**: Large files truncated to prevent leakage

### Minimal Permissions
```yaml
permissions:
  contents: read       # Read IaC files
  pull-requests: write # Post PR comments
```

### Safe PR Handling
- `pull_request`: Read-only access (comments only)
- `pull_request_target`: Write access (diagram PRs) - checks out generator from base branch

### CI Security Checks
- `pip-audit`: Python dependency vulnerabilities
- `bandit`: Code security issues
- Dependabot: Automated dependency updates

## 📚 Documentation

- [Dynamic Spacing Guide](docs/DYNAMIC_SPACING.md) - Detailed spacing configuration
- [Quick Start Spacing](docs/QUICK_START_SPACING.md) - Quick spacing recipes
- [Spacing Examples](docs/SPACING_EXAMPLES.md) - Visual examples
- [Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md) - Technical details
- [Testing Guide](TESTING.md) - Test suite documentation
- [Changelog](CHANGELOG.md) - Version history

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Release Process

1. Update [CHANGELOG.md](CHANGELOG.md)
2. Ensure CI is green
3. Create and push tag: `git tag v1.2.3 && git push origin v1.2.3`
4. GitHub Actions creates release and moves `v1` tag

## 📄 License

[License](LICENSE)

## 🔗 Related Projects

- [diagrams](https://diagrams.mingrammer.com/) - Diagram as code library
- [Graphviz](https://graphviz.org/) - Graph visualization
- [Mermaid](https://mermaid.js.org/) - Markdown diagrams
- [python-hcl2](https://github.com/amplify-education/python-hcl2) - Terraform parser

## 💡 Tips & Tricks

### Optimize Diagram Size

For large architectures, use `force_full: false` to only render changed resources:
```yaml
with:
  force_full: false
  direction: AUTO
```

### Debug Layout Issues

Enable debug output to see layout decisions:
```yaml
env:
  AUTO_ARCH_DEBUG: "1"
```

Output shows:
- Direction selection reasoning (LR vs TB)
- Complexity metrics (nodes, edges, depth)
- Spacing calculations (pad, nodesep, ranksep)
- VPC/subnet grouping logic

### Custom Icon Paths

Add custom provider icons in `icons/{provider}/` directory:
```
icons/
  aws/
    my_custom_service.png
  azure/
    my_custom_service.png
```

Icon mapping: `resource_type` → `icons/{provider}/{resource_type_without_prefix}.png`

Example: `aws_custom_service` → `icons/aws/custom_service.png`

### Performance Tuning

For very large diagrams (100+ resources):
- Use `image_formats: png` (skip SVG/JPG)
- Set `graph.overlap_removal: false`
- Use `graph.edge_routing: spline` (faster than ortho)
- Increase `limits.max_files` if needed

## 🎓 Examples Gallery

### Serverless Website Architectures

Professional serverless website implementations across providers:

- **AWS**: [terraform](examples/serverless-website/aws/terraform), [cloudformation](examples/serverless-website/aws/cloudformation)
- **Azure**: [terraform](examples/serverless-website/azure/terraform), [bicep](examples/serverless-website/azure/bicep)
- **GCP**: [terraform](examples/serverless-website/gcp/terraform)
- **IBM**: [terraform](examples/serverless-website/ibm/terraform)
- **OCI**: [terraform](examples/serverless-website/oci/terraform)

See [examples/serverless-website/README.md](examples/serverless-website/README.md) for details.

### Reference Architectures

- **AWS Basic**: VPC with public/private subnets, ALB, EC2, RDS
- **Multi-Cloud Complex**: AWS + Azure + GCP with cross-cloud connections
- **Serverless**: Lambda/Functions + API Gateway + storage

All examples include generated diagrams (MD, PNG, SVG).

## 🐛 Troubleshooting

**Issue**: Diagram not generated
- Check workflow logs for Python errors
- Verify Graphviz is installed (`which dot`)
- Ensure `.tf` files are valid HCL2

**Issue**: Wrong layout orientation
- Use `direction: AUTO` for intelligent selection
- Or manually specify `LR`, `TB`, `RL`, `BT`
- Check `AUTO_ARCH_DEBUG=1` output

**Issue**: Resources not grouped in VPC
- Verify VPC has `vpc_id` reference in subnet
- Check subnet has `subnet_id` reference in resource
- Ensure resource types match patterns (aws_vpc, aws_subnet)

**Issue**: Colors too light/dark
- Adjust in `.auto-arch-diagram.yml`:
  ```yaml
  render:
    # Semi-transparent colors with alpha channel
    color_aws: "#FFE8D699"
    color_vpc: "#E3F2FD77"
  ```

**Issue**: Too much spacing
- Use manual spacing instead of auto:
  ```yaml
  render:
    graph:
      pad: 0.3
      nodesep: 0.4
      ranksep: 0.8
  ```

---

**Made with ❤️ for Infrastructure Engineers**
