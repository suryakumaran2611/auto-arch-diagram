<div align="center">

# 🏗️ auto-arch-diagram

**Transform Infrastructure-as-Code into Beautiful Architecture Diagrams**

[![Python Tests](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/python-tests.yml/badge.svg)](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/python-tests.yml)
[![Secret Scan](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/suryakumaran2611/auto-arch-diagram/actions/workflows/secret-scan.yml)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-red.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[📖 User Guide](docs/USER_GUIDE.md) • [🌐 GitHub Pages](https://suryakumaran2611.github.io/auto-arch-diagram/)

*Automatically generate professional diagrams from Terraform, CloudFormation, Bicep, and Pulumi*

---

### 🌟 See It In Action

</div>

<table>
<tr>
<td width="50%">

**MLOps Multi-Cloud** (47 resources - PNG only)

![MLOps Multi-Cloud](examples/terraform/mlops-multi-cloud/architecture-diagram.png)

*AWS SageMaker + Azure AKS + GCP BigQuery (PNG only due to complexity)*

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
- 🎨 **Open Sans Bold Typography** - Enhanced readability with professional bold fonts
- ☁️ **Enhanced CloudFormation** - Full icon support and intelligent arrow styling
- 🚀 **GitHub Actions** - One-line workflow integration with PR comments
- 🔒 **Security-First** - Secret scanning, redaction, minimal permissions
- 🤖 **AI Mode** - Experimental AI-powered diagram generation
- 📚 **Comprehensive Docs** - Detailed [User Guide](docs/USER_GUIDE.md) available

### 🎨 Recent Improvements

**Typography Enhancement**: Upgraded to **Open Sans Bold** font for enhanced readability and professional appearance across all diagram formats.

**CloudFormation Excellence**: Enhanced CloudFormation support with:
- Full service-specific icon mapping (S3, Lambda, CloudFront, WAF, etc.)
- Intelligent arrow styling matching Terraform diagrams
- Improved layout consistency across IaC formats

**SVG Icon Embedding**: Fixed SVG diagrams to properly embed icons as base64 data URIs, ensuring portability and correct display in all viewers.

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
  workflow_dispatch:  # Manual trigger with force option
    inputs:
      force_update:
        description: 'Force diagram update even if no IaC files changed'
        type: boolean
        default: false

jobs:
  diagram:
### Publishing Diagrams to Confluence Pages

You can automatically publish or replace architecture diagrams to a Confluence page using the workflow's Confluence integration feature. This is useful for keeping your documentation up-to-date with the latest infrastructure changes.

**Example Workflow Step:**

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
```

**How it works:**
- Set `publish_enabled: true` and `publish_confluence: true` to activate Confluence publishing.
- Provide your Confluence instance URL, user, and API token as secrets.
- Specify the target page ID with `confluence_page_id`.
- Set `confluence_replace: true` to overwrite the existing diagram, or omit for append mode.

**Required Secrets:**
- `CONFLUENCE_URL`: Base URL of your Confluence instance (e.g., `https://your-domain.atlassian.net/wiki`)
- `CONFLUENCE_USER`: Confluence username or email
- `CONFLUENCE_TOKEN`: API token generated from Confluence

**Notes:**
- The workflow will upload the generated diagram (PNG/SVG/Markdown) to the specified Confluence page after each run.
- For more details, see the [User Guide](docs/USER_GUIDE.md#confluence-integration).
    permissions:
      contents: read
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
    with:
      direction: AUTO                 # Intelligent layout
      image_formats: png,svg
      comment_on_pr: true
      force_full: ${{ github.event.inputs.force_update || false }}  # Force generation if manually triggered
```

📖 **For complete documentation, see the [User Guide](docs/USER_GUIDE.md)**

**What this does:**
- 🔄 **Triggers on PRs** that modify IaC files
- 🎯 **Intelligent AUTO layout** chooses optimal orientation
- 📊 **Generates PNG + SVG** with embedded cloud icons
- 💬 **Posts diagram as PR comment** for easy review
- 🔒 **Minimal permissions** (read-only + PR comments)
- ⚠️ **Complexity limits**: Skips diagrams with >45 resources for performance

### Configuration Examples

**Multi-Cloud with Custom Paths**
```yaml
with:
  direction: AUTO
  image_formats: png,svg
  iac_globs: |
    infrastructure/terraform/**/*.tf
    cloudformation/**/*.yaml
    pulumi/**/*.py
    cdk/**/*.ts
  out_md: docs/architecture/diagram.md
```

**Production-Ready (Recommended)**
```yaml
name: Architecture Diagrams

on:
  pull_request:
    paths: ['**/*.tf', '**/*.bicep']
  workflow_dispatch:
    inputs:
      force_update:
        type: boolean
        default: false

jobs:
  diagram:
    permissions:
      contents: read
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
    with:
      direction: AUTO
      image_formats: png,svg
      comment_on_pr: true
      force_full: ${{ github.event.inputs.force_update || false }}
```

**Mermaid-Only (Fastest)**
```yaml
with:
  mode: static
  image_formats: none
  out_dir: artifacts
```

**AI Mode (Experimental)** ⚠️
> **Not for Production Use** - See [Security Considerations](docs/USER_GUIDE.md#security-considerations)

```yaml
with:
  mode: ai
  model: gpt-4o-mini
  direction: AUTO
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}  # Transmits IaC code to external services
```

**Diagram Update PR (Auto-commit)**
```yaml
on:
  pull_request_target:  # For fork safety
    paths: ['**/*.tf', '**/*.bicep']

jobs:
  diagram_pr:
    permissions:
      contents: write
      pull-requests: write
    uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
    with:
      direction: AUTO
      publish_enabled: true
      create_diagram_pr: true
      # comment_on_pr: false  # Only create PR, don't comment
```

**Force Updates (Repository Variable)**
```yaml
# Repository Settings → Variables → AUTO_ARCH_FORCE_UPDATE = true
# Then workflow will update on every push to main/develop
on:
  push:
    branches: [main, develop]
    if: vars.AUTO_ARCH_FORCE_UPDATE == 'true'
```

### 🧪 CI/CD Testing Workflow

**Complete CI Pipeline with Architecture Diagram Testing**
```yaml
name: CI Pipeline with Architecture Testing

on:
  pull_request:
    branches: [main]
    paths:
      - 'terraform/**'
      - 'bicep/**'
      - '**/template.yaml'
  workflow_dispatch: # Manual trigger

jobs:
  # Security and Quality Checks
  quality-checks:
    name: Quality Checks
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Terraform Security Scan
        uses: bridgecrewio/checkov-action@master
        with:
          directory: terraform/
          framework: terraform
          quiet: true
      
      - name: Terraform Format Check
        run: |
          cd terraform
          terraform fmt -check
          
      - name: Terraform Validation
        run: |
          cd terraform
          terraform validate

  # Architecture Diagram Generation
  architecture-diagram:
    name: Generate Architecture Diagram
    runs-on: ubuntu-latest
    needs: quality-checks
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate Architecture Diagram
        uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
        with:
          direction: AUTO
          image_formats: png,svg
          comment_on_pr: true
          # Only processes changed IaC files (default behavior)

  # Integration Tests
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: [quality-checks, architecture-diagram]
    if: github.event_name == 'pull_request'
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: latest
      
      - name: Terraform Plan
        run: |
          cd terraform
          terraform init -backend=false
          terraform plan -out=plan.tfplan
        env:
          AWS_DEFAULT_REGION: us-east-1
          TF_VAR_environment: test

      - name: Validate Diagram Resources
        run: |
          echo "Checking if diagram resources match terraform plan..."
          # Add custom validation logic here
          
  # Deploy to Staging (on main branch)
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [quality-checks, architecture-diagram, integration-tests]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: staging
    permissions:
      contents: read
      deployments: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Staging
        run: |
          echo "Deploying to staging environment..."
          # Add your deployment commands here
```

**Manual Testing Workflow**
```yaml
name: Manual Architecture Testing

on:
  workflow_dispatch:
    inputs:
      test_type:
        description: 'Type of test to run'
        required: true
        default: 'incremental'
        type: choice
        options:
          - incremental    # Only changed files (default)
          - full          # Force regenerate all diagrams
          - ai_mode       # Use AI generation (experimental)

jobs:
  test-architecture:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate Test Diagram
        uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
        with:
          direction: AUTO
          image_formats: png,jpg,svg
          force_full: ${{ github.event.inputs.test_type == 'full' }}
          mode: ${{ github.event.inputs.test_type == 'ai_mode' && 'ai' || 'static' }}
          comment_on_pr: ${{ github.event_name == 'pull_request' }}
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

**Multi-Environment Pipeline**
```yaml
name: Multi-Environment CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'terraform/**'
  pull_request:
    branches: [main]

env:
  # Different configurations per environment
  AWS_REGION: ${{ github.ref == 'refs/heads/main' && 'us-east-1' || 'us-west-2' }}
  ENVIRONMENT: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}

jobs:
  # Pre-commit checks
  pre-commit:
    name: Pre-commit Checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate Architecture for Review
        uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
        with:
          direction: AUTO
          image_formats: png
          comment_on_pr: true
          out_dir: architecture-review
  
  # Deploy and update diagrams
  deploy-and-diagram:
    name: Deploy and Update Architecture
    runs-on: ubuntu-latest
    needs: pre-commit
    if: github.event_name == 'push'
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy Infrastructure
        run: |
          echo "Deploying to ${{ env.ENVIRONMENT }}..."
          # Your deployment logic here
      
      - name: Update Architecture Documentation
        uses: suryakumaran2611/auto-arch-diagram/.github/workflows/reusable-auto-arch-diagram.yml@v1
        with:
          direction: AUTO
          image_formats: png,svg
          create_diagram_pr: true
          publish_enabled: true
          out_md: docs/architecture/${{ env.ENVIRONMENT }}/diagram.md
          out_png: assets/images/architecture-${{ env.ENVIRONMENT }}.png
```

**CI/CD Best Practices**
- ✅ **Quality gates before diagram generation** - Security scans, format checks, validation
- ✅ **Parallel execution** - Quality checks run in parallel with diagram generation
- ✅ **Environment-aware** - Different configs for staging vs production
- ✅ **Manual triggers** - `workflow_dispatch` for testing and debugging
- ✅ **Proper permissions** - Minimal permissions for each job
- ✅ **Artifact management** - Store diagrams as artifacts and in documentation
- ✅ **Dependency management** - `needs` ensures proper execution order

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
    cloud_run.png
```

**Icon Mapping Logic**
- Resource: `aws_my_custom_service` → Icon: `icons/aws/my_custom_service.png`
- Resource: `azure_custom_database` → Icon: `icons/azure/custom_database.png`
- Resource: `gcp_cloud_run` → Icon: `icons/gcp/cloud_run.png`

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

### Prerequisites
- **Python 3.11+** with PowerShell access
- **uv** (recommended) - Modern Python package installer
- Or traditional **pip** with virtual environment

### Setup with uv (Recommended)

**1. Create Virtual Environment**
```powershell
# Navigate to project directory
cd auto-arch-diagram

# Create virtual environment with specific Python
uv venv --python "3.12" --seed 3.12.11

# Alternative with full Python path
uv venv --python "C:/Python/cpython-3.12.11-windows-x86_64-none/python.exe"

# Traditional method (fallback)
python -m venv .venv
```

**2. Activate Environment**
```powershell
# Activate in current PowerShell session
.venv\Scripts\activate

# Verify activation (should show (.venv) in prompt)
python --version
```

**3. Install Dependencies**
```powershell
# Install all required packages
uv pip install python-hcl2 pytest graphviz diagrams

# Install additional dependencies for AI mode
uv pip install -r requirements-ai.txt

# Install development dependencies
uv pip install -r requirements-dev.txt
```

### Setup with pip (Traditional)

```powershell
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install python-hcl2 pytest graphviz diagrams

# Install AI dependencies
pip install -r requirements-ai.txt

# Install development dependencies  
pip install -r requirements-dev.txt
```

### Generate Diagrams Locally

```powershell
# Generate from example directory
python tools/generate_arch_diagram.py --iac-root examples --out-md diagram.md --out-png diagram.png

# Test with AI mode (requires OPENAI_API_KEY)
$env:OPENAI_API_KEY = "your-api-key"
python tools/generate_arch_diagram.py --mode ai --iac-root examples/test-ai-ml-blockchain --out-md ai-diagram.md

# Generate all formats
python tools/generate_arch_diagram.py --iac-root examples --out-md full-diagram.md --out-png full-diagram.png --out-svg full-diagram.svg --out-jpg full-diagram.jpg
```

### Testing the New Services

```powershell
# Test AI/ML/Blockchain service mapping
python tools/generate_arch_diagram.py --iac-root examples/test-ai-ml-blockchain --direction LR --out-md test-services.md

# Verify all services are recognized
python tools/generate_arch_diagram.py --mode ai --iac-root examples/test-ai-ml-blockchain --direction AUTO --out-md ai-test.md
```

### Traditional Linux/macOS Setup

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

### Robust Confluence Image Replacement

You can replace a specific image in a Confluence page using a unique marker or filename. This ensures only the intended diagram is updated, even if the page contains multiple images.

**Example Workflow Step:**

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

**How it works:**
- The workflow will search for the marker or filename in the Confluence page and replace only that image.
- If the marker is not found, it will fall back to replacing the first image or prepend the new image.
- Use a unique marker for each diagram to avoid accidental replacement of other images.

**Best Practices:**
- Always use a unique marker for each diagram type or environment.
- Store Confluence credentials as repository secrets.
- Test the workflow with a test page before using in production.

**Troubleshooting:**
- If the image is not replaced, check that the marker matches exactly in the page source.
- Ensure the page ID and credentials are correct.
- Review workflow logs for error messages from the Confluence API.

**Required Secrets:**
- `CONFLUENCE_URL`: Base URL of your Confluence instance (e.g., `https://your-domain.atlassian.net/wiki`)
- `CONFLUENCE_USER`: Confluence username or email
- `CONFLUENCE_TOKEN`: API token generated from Confluence

**Environment Variables:**
- `CONFLUENCE_IMAGE_MARKER`: (Optional) Unique marker to target a specific image for replacement.

**For full details and advanced usage, see the [User Guide](docs/USER_GUIDE.md#confluence-publishing-and-image-replacement).**

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

## 🚀 Upcoming Features

### 🤖 Enhanced AI Capabilities
- **Multiple AI Providers**: Claude, Gemini, and local AI models support
- **Advanced Analysis**: Better understanding of complex architectural patterns  
- **Custom Prompts**: User-defined AI prompts for specialized diagrams
- **Smart Layouts**: AI-driven layout optimization

### 🔌 Integration Expansions
- **Confluence Integration**: Automatic diagram publishing to Confluence pages
- **Notion Integration**: Direct updates to Notion databases and pages
- **Slack/Discord**: Diagram sharing and notifications in team channels
- **Jira Integration**: Link diagrams to Jira tickets and documentation

### 📊 Advanced Features
- **Cost Estimation**: Integration with cloud pricing APIs
- **Security Insights**: Automated security recommendations
- **Compliance Checking**: Compliance overlays and certifications
- **Version Comparison**: Visual diff between diagram versions

## ⚠️ Experimental Features

### 🧠 AI Mode (Experimental)
> **Not for Production Use** - See [User Guide](docs/USER_GUIDE.md#ai-mode-experimental) for details

- **Status**: Experimental - May contain inaccuracies
- **Security**: Transmits IaC code to external AI services  
- **Costs**: API charges may apply
- **Recommendation**: Use for testing and evaluation only

**Known Limitations:**
- May miss complex architectural relationships
- Generated diagrams require manual review
- Not suitable for production environments
- API costs can accumulate quickly

---

<div align="center">

**Made with ❤️ for Infrastructure Engineers**

**Copyright © 2024-2026 SuryaKumaran SivaKumararan**

⭐ **Star this repo** if you find it useful!

[📖 Documentation](docs/) • [🐛 Report Bug](https://github.com/suryakumaran2611/auto-arch-diagram/issues) • [💡 Request Feature](https://github.com/suryakumaran2611/auto-arch-diagram/issues)

</div>
