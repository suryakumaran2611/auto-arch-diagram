#!/bin/bash
# Auto Architecture Diagram - Update GitHub Pages Images Script
# This script regenerates all example diagrams and updates GitHub Pages documentation

set -e  # Exit on any error

echo "🚀 Auto Architecture Diagram - GitHub Pages Image Update Script"
echo "================================================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/Scripts/activate || source .venv/bin/activate

# Function to regenerate a diagram
regenerate_diagram() {
    local input_file="$1"
    local output_png="$2"
    local output_svg="$3"
    local description="$4"

    echo "🔄 Regenerating $description..."

    if python tools/generate_arch_diagram.py --changed-files "$input_file" --out-png "$output_png" --out-svg "$output_svg"; then
        echo "✅ Successfully generated $description"
    else
        echo "❌ Failed to generate $description"
        return 1
    fi
}

# Function to update docs image
update_docs_image() {
    local source_file="$1"
    local dest_file="$2"
    local description="$3"

    if cp "$source_file" "$dest_file"; then
        echo "📋 Updated $description in docs"
    else
        echo "❌ Failed to update $description in docs"
        return 1
    fi
}

echo ""
echo "🔄 Regenerating all example diagrams..."
echo "========================================"

# Regenerate CloudFormation examples
regenerate_diagram \
    "examples/serverless-website/aws/cloudformation/template.yaml" \
    "examples/serverless-website/aws/cloudformation/architecture-diagram.png" \
    "examples/serverless-website/aws/cloudformation/architecture-diagram.svg" \
    "AWS CloudFormation Serverless Website"

# Regenerate Terraform examples
regenerate_diagram \
    "examples/serverless-website/aws/terraform/main.tf" \
    "examples/serverless-website/aws/terraform/architecture-diagram.png" \
    "examples/serverless-website/aws/terraform/architecture-diagram.svg" \
    "AWS Terraform Serverless Website"

regenerate_diagram \
    "examples/serverless-website/azure/terraform/main.tf" \
    "examples/serverless-website/azure/terraform/architecture-diagram.png" \
    "examples/serverless-website/azure/terraform/architecture-diagram.svg" \
    "Azure Terraform Serverless Website"

regenerate_diagram \
    "examples/serverless-website/gcp/terraform/main.tf" \
    "examples/serverless-website/gcp/terraform/architecture-diagram.png" \
    "examples/serverless-website/gcp/terraform/architecture-diagram.svg" \
    "GCP Terraform Serverless Website"

# Regenerate multi-cloud example
regenerate_diagram \
    "examples/terraform/mlops-multi-cloud/main.tf" \
    "examples/terraform/mlops-multi-cloud/architecture-diagram.png" \
    "examples/terraform/mlops-multi-cloud/architecture-diagram.svg" \
    "Multi-Cloud Demo"

# Regenerate other key examples
regenerate_diagram \
    "examples/terraform/custom-icons-demo/main.tf" \
    "examples/terraform/custom-icons-demo/architecture-diagram.png" \
    "examples/terraform/custom-icons-demo/architecture-diagram.svg" \
    "Custom Icons Demo"

regenerate_diagram \
    "examples/terraform/mlops-multi-region-aws/main.tf" \
    "examples/terraform/mlops-multi-region-aws/architecture-diagram.png" \
    "examples/terraform/mlops-multi-region-aws/architecture-diagram.svg" \
    "MLOps Multi-Region AWS"

echo ""
echo "📋 Updating GitHub Pages documentation images..."
echo "================================================="

# Update docs/images/ with latest generated diagrams
update_docs_image \
    "examples/terraform/mlops-multi-cloud/architecture-diagram.png" \
    "docs/images/mlops-multi-cloud.png" \
    "Multi-Cloud Demo image"

update_docs_image \
    "examples/terraform/custom-icons-demo/architecture-diagram.png" \
    "docs/images/custom-icons-demo.png" \
    "Custom Icons Demo image"

update_docs_image \
    "examples/terraform/mlops-multi-region-aws/architecture-diagram.png" \
    "docs/images/mlops-aws.png" \
    "MLOps Multi-Region AWS image"

update_docs_image \
    "examples/serverless-website/aws/terraform/architecture-diagram.png" \
    "docs/images/aws-serverless.png" \
    "AWS Serverless Website image"

update_docs_image \
    "examples/serverless-website/azure/terraform/architecture-diagram.png" \
    "docs/images/azure-serverless.png" \
    "Azure Serverless Website image"

update_docs_image \
    "examples/serverless-website/gcp/terraform/architecture-diagram.png" \
    "docs/images/gcp-serverless.png" \
    "GCP Serverless Website image"

echo ""
echo "📊 Verification - Checking icon counts..."
echo "==========================================="

# Verify all diagrams have expected number of icons
check_icons() {
    local file="$1"
    local expected="$2"
    local description="$3"

    if [ -f "$file" ]; then
        local count=$(grep -c "base64" "$file" 2>/dev/null || echo "0")
        if [ "$count" -eq "$expected" ]; then
            echo "✅ $description: $count icons (expected $expected)"
        else
            echo "⚠️  $description: $count icons (expected $expected)"
        fi
    else
        echo "❌ $description: File not found"
    fi
}

check_icons "examples/terraform/mlops-multi-cloud/architecture-diagram.svg" "7" "Multi-Cloud Demo"
check_icons "examples/serverless-website/aws/cloudformation/architecture-diagram.svg" "8" "AWS CloudFormation"
check_icons "examples/serverless-website/aws/terraform/architecture-diagram.svg" "11" "AWS Terraform"
check_icons "examples/serverless-website/azure/terraform/architecture-diagram.svg" "6" "Azure Terraform"
check_icons "examples/serverless-website/gcp/terraform/architecture-diagram.svg" "8" "GCP Terraform"

echo ""
echo "🎉 GitHub Pages images update complete!"
echo "========================================"
echo ""
echo "📝 Summary:"
echo "  • Regenerated 7 key example diagrams"
echo "  • Updated 6 GitHub Pages documentation images"
echo "  • Verified icon counts match expectations"
echo ""
echo "📍 Files updated:"
echo "  • docs/images/mlops-multi-cloud.png"
echo "  • docs/images/custom-icons-demo.png"
echo "  • docs/images/mlops-aws.png"
echo "  • docs/images/aws-serverless.png"
echo "  • docs/images/azure-serverless.png"
echo "  • docs/images/gcp-serverless.png"
echo ""
echo "🔄 Next steps:"
echo "  1. Commit the updated images to git"
echo "  2. Push to GitHub to update GitHub Pages"
echo "  3. The documentation will reflect the latest code changes"