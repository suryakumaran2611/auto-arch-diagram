<div align="center">

# 🏗️ auto-arch-diagram

**Transform Infrastructure-as-Code into Beautiful Architecture Diagrams**

[![Python Tests](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/python-tests.yml/badge.svg)](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/python-tests.yml)
[![Secret Scan](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/secret-scan.yml)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-red.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

*Automatically generate professional diagrams from Terraform, CloudFormation, Bicep, and Pulumi*

---

### 🌟 See It In Action

</div>

<table>
<tr>
<td width="50%">

**MLOps Multi-Cloud** (47 resources)

![MLOps Multi-Cloud](examples/terraform/mlops-multi-cloud/architecture-diagram.png)

*AWS SageMaker + Azure AKS + GCP BigQuery*

</td>
<td width="50%">

**Custom Icons Demo** (40+ resources)

![Custom Icons Demo](examples/terraform/custom-icons-demo/architecture-diagram.png)

*Event-driven serverless with 11 custom icons*

</td>
</tr>
<tr>
<td width="50%">

**MLOps Multi-Region AWS** (46 resources)

![MLOps Multi-Region](examples/terraform/mlops-multi-region-aws/architecture-diagram.png)

*Primary + DR with VPC peering*

</td>
<td width="50%">

**AWS Serverless Website**

![AWS Serverless](examples/serverless-website/aws/terraform/architecture-diagram.png)

*S3 + CloudFront + ACM*

</td>
</tr>
</table>

---

## ✨ Key Features

- 🎯 **VPC/Network Grouping** - Automatic VPC organization with subnet distinction
- 🧠 **AUTO Layout** - Intelligent orientation selection (6-factor analysis)
- 🏗️ **Multi-Cloud** - 2,100+ official icons for AWS, Azure, GCP, and more
- 📤 **Multiple Formats** - Mermaid, PNG, SVG, JPEG with embedded icons
- 🚀 **GitHub Actions** - One-line workflow integration with PR comments
- 🔒 **Security-First** - Secret scanning, redaction, minimal permissions

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

**What this does:**
- 🔄 **Triggers on PRs** that modify IaC files
- 🎯 **Intelligent AUTO layout** chooses optimal orientation
- 📊 **Generates PNG + SVG** with embedded cloud icons
- 💬 **Posts diagram as PR comment** for easy review
- 🔒 **Minimal permissions** (read-only + PR comments)

### Configuration Examples

**Multi-Cloud with Custom Paths**
```yaml
with:
  direction: AUTO
  image_formats: png,svg
  iac_globs: |
    infrastructure/terraform/**/*.tf
    cloudformation/**/*.yaml
  out_md: docs/architecture/diagram.md
```

**Mermaid-Only (Fastest)**
```yaml
with:
  mode: static
  image_formats: none
  out_dir: artifacts
```

**AI Mode**
```yaml
with:
  mode: ai
  model: gpt-4o-mini
  direction: AUTO
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

**Diagram Update PR**
```yaml
with:
  direction: AUTO
  publish_enabled: true
  create_diagram_pr: true
```

### 🎨 Custom Icons

**Add Custom Provider Icons**
```
icons/
  aws/
    my_custom_service.png
    another_service.png
  azure/
    custom_database.png
  gcp/
    special_processor.png
```

**Icon Mapping Logic**
- Resource: `aws_my_custom_service` → Icon: `icons/aws/my_custom_service.png`
- Resource: `azure_custom_database` → Icon: `icons/azure/custom_database.png`
- Resource: `gcp_special_processor` → Icon: `icons/gcp/special_processor.png`

**Supported Formats**
- PNG (recommended with transparency)
- SVG (vector graphics)
- JPG (for simple icons)

**Icon Naming Rules**
- Remove provider prefix: `aws_` → ``
- Use lowercase: `AWS_Service` → `service`
- Replace underscores with hyphens: `my_service` → `my-service` (optional)

## 📋 Configuration Reference

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `direction` | `LR` | `AUTO`, `LR`, `TB`, `RL`, `BT` |
| `mode` | `static` | `static` or `ai` (requires OPENAI_API_KEY) |
| `image_formats` | `png,jpg,svg` | Formats to generate or `none` |
| `force_full` | `false` | Render full architecture (ignore changes) |
| `comment_on_pr` | `true` | Post/update sticky PR comment |
| `create_diagram_pr` | `false` | Create diagram update PR |

### Default IaC File Patterns
```yaml
iac_globs: |
  **/*.tf              # Terraform
  **/*.bicep           # Bicep
  **/template.yaml     # CloudFormation
  **/Pulumi.yaml       # Pulumi YAML
  **/*.cdk.ts          # AWS CDK
```

### Required Permissions

```yaml
# Basic PR comments
permissions:
  contents: read
  pull-requests: write

# Diagram commits (advanced)
permissions:
  contents: write
  pull-requests: write
```

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

## 🎨 Architecture Features

### VPC/Network Grouping
Resources automatically organized within VPC/VNet/VCN containers:
- **VPC Clusters** - Auto-detect and group VPC resources
- **Subnet Grouping** - Public (dashed border) vs Private (solid border)
- **Resource Placement** - EC2, Lambda, RDS placed in correct subnets
- **Color Coding** - Semi-transparent provider colors

### Intelligent Edge Styling
- **Solid Lines** - Network connections (default)
- **Dashed Lines** - Security groups, firewalls, IAM policies (red)
- **Bold Lines** - Data flow to databases/storage (blue)
- **Dotted Lines** - Cross-cloud/cross-region dependencies (gray)

### AUTO Direction Selection
6-factor scoring chooses optimal orientation:
- **Horizontal (LR)** - Wide architectures, 4+ lanes, 50+ resources
- **Vertical (TB)** - Deep nesting, high edge density, few large clusters

### Multi-Cloud Support
- **2,100+ Official Icons** - AWS, Azure, GCP, IBM Cloud, Oracle Cloud
- **Custom Icons** - Add your own provider-specific icons
- **Color-Coded Providers** - AWS orange, Azure blue, GCP green

## 🏗️ Supported IaC

- **Terraform** - Full support (VPC grouping, 50+ AWS icons)
- **CloudFormation** - Full support (Ref, GetAtt, Sub, DependsOn)
- **Bicep** - Good support (resource, dependsOn, parent)
- **Pulumi YAML** - Good support (resources, dependsOn)
- **Pulumi TS/Py, CDK** - Limited support (requires AI mode)

## 📊 Examples

| Architecture | Resources | Features |
|--------------|-----------|----------|
| **MLOps Multi-Cloud** | 47 | AWS + Azure + GCP |
| **Custom Icons Demo** | 40+ | 11 custom icons |
| **MLOps Multi-Region** | 46 | Primary + DR |
| **Serverless Websites** | 6-8 | Multi-cloud comparison |

📁 **[View All Examples →](examples/README.md)**

## 🚀 Local Development

```bash
# Setup
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate diagram
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

# Run tests
pytest
```

## 🔒 Security

- **Secret Scanning** - gitleaks, automatic redaction, file truncation
- **Minimal Permissions** - Read-only access for basic use
- **Safe PR Handling** - Secure workflow isolation
- **CI Security** - pip-audit, bandit, Dependabot

## 📚 Documentation

- [Dynamic Spacing Guide](docs/DYNAMIC_SPACING.md)
- [Testing Guide](TESTING.md)
- [Changelog](CHANGELOG.md)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

**Creative Commons Attribution-NonCommercial 4.0 International License** - Non-commercial use only. Commercial use requires explicit written approval from SuryaKumaran SivaKumararan.

[View Full License](LICENSE) • [🔗 Related Projects](https://diagrams.mingrammer.com/)

## 💡 Tips & Tricks

### Performance Optimization
**Large Architectures (100+ resources)**
```yaml
with:
  force_full: false      # Only render changed resources
  image_formats: png    # Skip SVG/JPG for speed
```

**Advanced Performance Tuning**
```yaml
# In .auto-arch-diagram.yml
render:
  graph:
    overlap_removal: false    # Faster layout
    edge_routing: spline      # Faster than ortho
limits:
  max_files: 50              # Limit file processing
```

### Layout Optimization
**Best Practices**
```yaml
with:
  direction: AUTO           # Intelligent selection
  render_layout: lanes      # Category-first (default)
  render_bg: transparent    # Better for docs
```

**Debug Layout Issues**
```yaml
env:
  AUTO_ARCH_DEBUG: "1"     # Shows scoring details
```

Output shows:
- Direction selection reasoning (LR vs TB)
- Complexity metrics (nodes, edges, depth)
- Spacing calculations (pad, nodesep, ranksep)
- VPC/subnet grouping logic

### Custom Icons Deep Dive
**Directory Structure**
```
icons/
  aws/
    my_custom_service.png
    api-gateway.png
    lambda@edge.png
  azure/
    custom_function.png
    storage_account.png
  gcp/
    cloud_run.png
    bigtable.png
```

**Icon Resolution & Quality**
- **Recommended Size**: 64x64 to 128x128 pixels
- **Format**: PNG with transparency (best)
- **Background**: Transparent or white
- **Style**: Consistent with provider's design language

**Advanced Icon Mapping**
```yaml
# Custom icon mapping in .auto-arch-diagram.yml
icons:
  custom_mappings:
    aws_custom_api: "icons/aws/api-gateway.png"
    azure_serverless: "icons/azure/custom_function.png"
    gcp_ml_service: "icons/gcp/cloud-ml.png"
```

**Fallback Logic**
1. Check custom icon directory first
2. Fall back to built-in provider icons
3. Use generic resource type icon
4. Final fallback to default service icon

### Workflow Best Practices
**Choose Right Trigger**
```yaml
# PR reviews (recommended)
on:
  pull_request:
    paths: ['**/*.tf', '**/*.bicep']

# Automated diagram updates
on:
  pull_request_target:
    types: [opened, synchronize, reopened]
```

**Organize Output Files**
```yaml
# For documentation
with:
  out_md: docs/architecture/diagram.md
  out_png: assets/images/architecture.png

# For CI artifacts
with:
  out_dir: artifacts
  image_formats: png,svg
```



## 🐛 Troubleshooting

### Reusable Workflow Issues
**Workflow fails with "tool not found"**
- Ensure you're using `@v1` or specific tag: `@v1.2.3`
- Check workflow ref: `suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1`

**No IaC files detected**
- Verify `iac_globs` patterns match your file structure
- Check files are tracked by Git (`git ls-files`)
- Use `force_full: true` to ignore change detection

**PR comment not posted**
- Set `pull-requests: write` permission
- Check `comment_on_pr: true` is set
- Verify workflow triggers on `pull_request` event

### Diagram Generation Issues
**Diagram not generated**
- Check workflow logs for Python errors
- Verify Graphviz is installed (`which dot`)
- Ensure `.tf` files are valid HCL2

**Wrong layout orientation**
- Use `direction: AUTO` for intelligent selection
- Or manually specify `LR`, `TB`, `RL`, `BT`
- Check `AUTO_ARCH_DEBUG=1` output

**Resources not grouped in VPC**
- Verify VPC has `vpc_id` reference in subnet
- Check subnet has `subnet_id` reference in resource
- Ensure resource types match patterns (aws_vpc, aws_subnet)

**Custom icons not loading**
- Verify icon path: `icons/{provider}/{resource_type}.png`
- Check file naming (remove provider prefix)
- Ensure PNG format with transparency
- Check file permissions and Git tracking

### Debug Mode
```yaml
env:
  AUTO_ARCH_DEBUG: "1"  # Shows scoring details and file detection
```

### Performance Issues
**Large diagrams timeout**
- Use `image_formats: png` (skip SVG/JPG)
- Set `force_full: false` for incremental updates
- Increase `limits.max_files` if needed
- Use `graph.overlap_removal: false`

---

<div align="center">

**Made with ❤️ for Infrastructure Engineers**

**Copyright © 2024-2026 SuryaKumaran SivaKumararan**

⭐ **Star this repo** if you find it useful!

[📖 Documentation](docs/) • [🐛 Report Bug](https://github.com/suryakumaran2611/auto-arch-diagram/issues) • [💡 Request Feature](https://github.com/suryakumaran2611/auto-arch-diagram/issues)

</div>
