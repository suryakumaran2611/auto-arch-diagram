# GitHub Pages Image Update Scripts

This directory contains scripts to automatically update GitHub Pages documentation images with the latest generated diagrams from the current codebase.

## Available Scripts

### 1. `update_github_pages_images.sh` (Linux/macOS/Bash)
- **Platform**: Unix-like systems with Bash
- **Dependencies**: Bash shell, Python virtual environment
- **Usage**: `./update_github_pages_images.sh`

### 2. `update_github_pages_images.bat` (Windows)
- **Platform**: Windows with Command Prompt
- **Dependencies**: Windows CMD, Python virtual environment
- **Usage**: `update_github_pages_images.bat`

### 3. `update_github_pages_images.py` (Cross-Platform)
- **Platform**: Any system with Python 3.6+
- **Dependencies**: Python 3.6+, virtual environment
- **Usage**: `python update_github_pages_images.py`

## What the Scripts Do

### Phase 1: Diagram Regeneration
The scripts regenerate all key example diagrams with the latest code:

1. **AWS CloudFormation Serverless Website** (8 resources)
2. **AWS Terraform Serverless Website** (11 resources)
3. **Azure Terraform Serverless Website** (6 resources)
4. **GCP Terraform Serverless Website** (8 resources)
5. **Multi-Cloud Demo** (7 resources with network labels)
6. **Custom Icons Demo** (variable resources)
7. **MLOps Multi-Region AWS** (variable resources)

### Phase 2: Documentation Update
Updates GitHub Pages documentation images:

- `docs/images/mlops-multi-cloud.png`
- `docs/images/custom-icons-demo.png`
- `docs/images/mlops-aws.png`
- `docs/images/aws-serverless.png`
- `docs/images/azure-serverless.png`
- `docs/images/gcp-serverless.png`

### Phase 3: Verification
Validates that diagrams have the expected number of icons and reports any issues.

## Prerequisites

1. **Virtual Environment**: Ensure `.venv` exists and is activated
2. **Dependencies**: All Python dependencies installed
3. **Directory**: Run from the project root directory
4. **Permissions**: Write access to `docs/images/` and example directories

## Usage Examples

### Linux/macOS
```bash
# Make script executable (first time only)
chmod +x update_github_pages_images.sh

# Run the update script
./update_github_pages_images.sh
```

### Windows
```batch
# Run the update script
update_github_pages_images.bat
```

### Python (Cross-Platform)
```bash
# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run the update script
python update_github_pages_images.py
```

## Output Example

```
🚀 Auto Architecture Diagram - GitHub Pages Image Update Script
=================================================================

🔄 Regenerating all example diagrams...
=========================================
🔄 Regenerating AWS CloudFormation Serverless Website...
✅ Successfully generated AWS CloudFormation Serverless Website
🔄 Regenerating AWS Terraform Serverless Website...
✅ Successfully generated AWS Terraform Serverless Website
[... more diagrams ...]

📋 Updating GitHub Pages documentation images...
=================================================
📋 Updated Multi-Cloud Demo image in docs
📋 Updated Custom Icons Demo image in docs
[... more updates ...]

📊 Verification - Checking icon counts...
===========================================
✅ Multi-Cloud Demo: 7 icons (expected 7)
✅ AWS CloudFormation: 8 icons (expected 8)
✅ AWS Terraform: 11 icons (expected 11)
✅ Azure Terraform: 6 icons (expected 6)
✅ GCP Terraform: 8 icons (expected 8)

🎉 GitHub Pages images update complete!
=========================================

📝 Summary:
  • Regenerated 7 key example diagrams
  • Updated 6 GitHub Pages documentation images
  • Verified icon counts match expectations

📍 Files updated:
  • docs/images/mlops-multi-cloud.png
  • docs/images/custom-icons-demo.png
  • docs/images/mlops-aws.png
  • docs/images/aws-serverless.png
  • docs/images/azure-serverless.png
  • docs/images/gcp-serverless.png

🔄 Next steps:
  1. Commit the updated images to git
  2. Push to GitHub to update GitHub Pages
  3. The documentation will reflect the latest code changes
```

## Files Updated

### Example Diagrams (PNG + SVG)
- `examples/serverless-website/aws/cloudformation/architecture-diagram.*`
- `examples/serverless-website/aws/terraform/architecture-diagram.*`
- `examples/serverless-website/azure/terraform/architecture-diagram.*`
- `examples/serverless-website/gcp/terraform/architecture-diagram.*`
- `examples/terraform/mlops-multi-cloud/architecture-diagram.*`
- `examples/terraform/custom-icons-demo/architecture-diagram.*`
- `examples/terraform/mlops-multi-region-aws/architecture-diagram.*`

### GitHub Pages Documentation
- `docs/images/mlops-multi-cloud.png`
- `docs/images/custom-icons-demo.png`
- `docs/images/mlops-aws.png`
- `docs/images/aws-serverless.png`
- `docs/images/azure-serverless.png`
- `docs/images/gcp-serverless.png`

## Expected Icon Counts

The scripts verify diagrams have the correct number of icons:

- **Multi-Cloud Demo**: 7 icons
- **AWS CloudFormation**: 8 icons
- **AWS Terraform**: 11 icons
- **Azure Terraform**: 6 icons
- **GCP Terraform**: 8 icons

## Troubleshooting

### Virtual Environment Issues
```bash
# Recreate virtual environment if needed
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Permission Issues
```bash
# Ensure write permissions
chmod -R u+w docs/images/
chmod -R u+w examples/
```

### Script Fails to Run
- Ensure you're in the project root directory
- Check that `tools/generate_arch_diagram.py` exists
- Verify Python virtual environment is activated

## Integration with CI/CD

These scripts can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Update GitHub Pages Images
  run: |
    python update_github_pages_images.py
    git add docs/images/*.png examples/**/*.png
    git commit -m "Update diagrams with latest code changes" || true
    git push
```

## Manual Alternative

If you prefer to run commands manually:

```bash
# Regenerate diagrams
python tools/generate_arch_diagram.py --changed-files examples/terraform/mlops-multi-cloud/main.tf --out-png examples/terraform/mlops-multi-cloud/architecture-diagram.png

# Update docs
cp examples/terraform/mlops-multi-cloud/architecture-diagram.png docs/images/mlops-multi-cloud.png

# Verify
grep -c "base64" examples/terraform/mlops-multi-cloud/architecture-diagram.svg
```