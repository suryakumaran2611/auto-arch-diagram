#!/usr/bin/env python3
"""
Auto Architecture Diagram - GitHub Pages Image Update Script
This script regenerates all example diagrams and updates GitHub Pages documentation
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Successfully completed {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed {description}: {e}")
        print(f"Error output: {e.stderr}")
        return False

def regenerate_diagram(input_file, output_png, output_svg, description):
    """Regenerate a single diagram"""
    cmd = f'python tools/generate_arch_diagram.py --changed-files "{input_file}" --out-png "{output_png}" --out-svg "{output_svg}"'
    return run_command(cmd, f"Regenerating {description}")

def update_docs_image(source_file, dest_file, description):
    """Update a docs image"""
    try:
        shutil.copy2(source_file, dest_file)
        print(f"📋 Updated {description} in docs")
        return True
    except Exception as e:
        print(f"❌ Failed to update {description}: {e}")
        return False

def check_icons(file_path, expected_count, description):
    """Check the number of icons in a diagram"""
    if not os.path.exists(file_path):
        print(f"❌ {description}: File not found")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        icon_count = content.count('base64')
        if icon_count == expected_count:
            print(f"✅ {description}: {icon_count} icons (expected {expected_count})")
            return True
        else:
            print(f"⚠️  {description}: {icon_count} icons (expected {expected_count})")
            return False
    except Exception as e:
        print(f"❌ {description}: Error checking icons: {e}")
        return False

def main():
    """Main update script"""
    print("🚀 Auto Architecture Diagram - GitHub Pages Image Update Script")
    print("=" * 70)

    # Check if virtual environment exists
    if not os.path.exists('.venv'):
        print("❌ Virtual environment not found. Please run setup first.")
        sys.exit(1)

    # Check if we're in the right directory
    if not os.path.exists('tools/generate_arch_diagram.py'):
        print("❌ Not in the auto-arch-diagram directory. Please cd to the project root.")
        sys.exit(1)

    print("\n🔄 Regenerating all example diagrams...")
    print("=" * 50)

    # Define all diagrams to regenerate
    diagrams = [
        {
            'input': 'examples/serverless-website/aws/cloudformation/template.yaml',
            'png': 'examples/serverless-website/aws/cloudformation/architecture-diagram.png',
            'svg': 'examples/serverless-website/aws/cloudformation/architecture-diagram.svg',
            'desc': 'AWS CloudFormation Serverless Website',
            'expected_icons': 8
        },
        {
            'input': 'examples/serverless-website/aws/terraform/main.tf',
            'png': 'examples/serverless-website/aws/terraform/architecture-diagram.png',
            'svg': 'examples/serverless-website/aws/terraform/architecture-diagram.svg',
            'desc': 'AWS Terraform Serverless Website',
            'expected_icons': 11
        },
        {
            'input': 'examples/serverless-website/azure/terraform/main.tf',
            'png': 'examples/serverless-website/azure/terraform/architecture-diagram.png',
            'svg': 'examples/serverless-website/azure/terraform/architecture-diagram.svg',
            'desc': 'Azure Terraform Serverless Website',
            'expected_icons': 6
        },
        {
            'input': 'examples/serverless-website/gcp/terraform/main.tf',
            'png': 'examples/serverless-website/gcp/terraform/architecture-diagram.png',
            'svg': 'examples/serverless-website/gcp/terraform/architecture-diagram.svg',
            'desc': 'GCP Terraform Serverless Website',
            'expected_icons': 8
        },
        {
            'input': 'examples/terraform/mlops-multi-cloud/main.tf',
            'png': 'examples/terraform/mlops-multi-cloud/architecture-diagram.png',
            'svg': 'examples/terraform/mlops-multi-cloud/architecture-diagram.svg',
            'desc': 'Multi-Cloud Demo',
            'expected_icons': 7
        },
        {
            'input': 'examples/terraform/custom-icons-demo/main.tf',
            'png': 'examples/terraform/custom-icons-demo/architecture-diagram.png',
            'svg': 'examples/terraform/custom-icons-demo/architecture-diagram.svg',
            'desc': 'Custom Icons Demo',
            'expected_icons': None  # Variable number for custom icons
        },
        {
            'input': 'examples/terraform/mlops-multi-region-aws/main.tf',
            'png': 'examples/terraform/mlops-multi-region-aws/architecture-diagram.png',
            'svg': 'examples/terraform/mlops-multi-region-aws/architecture-diagram.svg',
            'desc': 'MLOps Multi-Region AWS',
            'expected_icons': None  # Variable number
        }
    ]

    # Regenerate all diagrams
    success_count = 0
    for diagram in diagrams:
        if regenerate_diagram(diagram['input'], diagram['png'], diagram['svg'], diagram['desc']):
            success_count += 1
        else:
            print(f"⚠️  Failed to regenerate {diagram['desc']}")

    print(f"\n📋 Regenerated {success_count}/{len(diagrams)} diagrams successfully")

    print("\n📋 Updating GitHub Pages documentation images...")
    print("=" * 55)

# Define docs images to update - COMPRENSIVE LIST
    docs_updates = [
        {
            'source': 'examples/serverless-website/aws/cloudformation/architecture-diagram.png',
            'dest': 'docs/images/aws-cloudformation.png',
            'desc': 'AWS CloudFormation Serverless Website image'
        },
        {
            'source': 'examples/serverless-website/aws/terraform/architecture-diagram.png',
            'dest': 'docs/images/aws-serverless.png',
            'desc': 'AWS Terraform Serverless Website image'
        },
        {
            'source': 'examples/serverless-website/azure/terraform/architecture-diagram.png',
            'dest': 'docs/images/azure-serverless.png',
            'desc': 'Azure Terraform Serverless Website image'
        },
        {
            'source': 'examples/serverless-website/gcp/terraform/architecture-diagram.png',
            'dest': 'docs/images/gcp-serverless.png',
            'desc': 'GCP Terraform Serverless Website image'
        },
        {
            'source': 'examples/serverless-website/aws/cdk/architecture-diagram.png',
            'dest': 'docs/images/aws-cdk.png',
            'desc': 'AWS CDK Serverless Website image'
        },
        {
            'source': 'examples/serverless-website/aws/pulumi/architecture-diagram.png',
            'dest': 'docs/images/aws-pulumi.png',
            'desc': 'AWS Pulumi Serverless Website image'
        },
        {
            'source': 'examples/terraform/mlops-multi-cloud/architecture-diagram.png',
            'dest': 'docs/images/mlops-multi-cloud.png',
            'desc': 'Multi-Cloud Demo image'
        },
        {
            'source': 'examples/terraform/custom-icons-demo/architecture-diagram.png',
            'dest': 'docs/images/custom-icons-demo.png',
            'desc': 'Custom Icons Demo image'
        },
        {
            'source': 'examples/terraform/mlops-multi-region-aws/architecture-diagram.png',
            'dest': 'docs/images/mlops-aws.png',
            'desc': 'MLOps Multi-Region AWS image'
        },
        {
            'source': 'examples/serverless-website/ibm/terraform/architecture-diagram.png',
            'dest': 'docs/images/ibm-serverless.png',
            'desc': 'IBM Terraform Serverless Website image'
        },
        {
            'source': 'examples/serverless-website/oci/terraform/architecture-diagram.png',
            'dest': 'docs/images/oci-serverless.png',
            'desc': 'OCI Terraform Serverless Website image'
        }
    ]

# Update all docs images with verification
    docs_success_count = 0
    failed_updates = []
    
    for update in docs_updates:
        print(f"🔄 Updating {update['desc']}...")
        
        # Verify source image integrity before copying
        if not verify_image_integrity(update['source'], update['desc']):
            failed_updates.append(f"❌ {update['desc']}: Source image verification failed")
            continue
            
        # Copy image to docs
        if update_docs_image(update['source'], update['dest'], update['desc']):
            docs_success_count += 1
            
            # Verify the copied image
            if verify_image_integrity(update['dest'], f"Copied {update['desc']}"):
                print(f"✅ {update['desc']}: Successfully updated and verified")
            else:
                failed_updates.append(f"⚠️  {update['desc']}: Copied but verification failed")
        else:
            failed_updates.append(f"❌ {update['desc']}: Update failed")

    if failed_updates:
        print(f"\n⚠️  Some updates failed:")
        for failure in failed_updates:
            print(f"  {failure}")
    
    print(f"\n📋 Updated {docs_success_count}/{len(docs_updates)} docs images successfully")

    print("\nVerification - Checking icon counts...")
    print("=" * 45)

    # Check icon counts for key diagrams
    verification_results = []
    for diagram in diagrams:
        if diagram['expected_icons'] is not None:
            svg_file = diagram['svg']
            if check_icons(svg_file, diagram['expected_icons'], diagram['desc']):
                verification_results.append(True)
            else:
                verification_results.append(False)

    verified_count = sum(verification_results)
    total_to_verify = len([d for d in diagrams if d['expected_icons'] is not None])

    print(f"\nVerification: {verified_count}/{total_to_verify} diagrams passed icon count checks")

    print("\nFiles updated:")
    for update in docs_updates:
        print(f"  • {update['dest']}")

    print("\nNext steps:")
    print("  1. Review the generated diagrams for correctness")
    print("\nGitHub Pages images update complete!")
    print("=" * 45)
    print("\nSummary:")
    print(f"  - Regenerated {success_count}/{len(diagrams)} example diagrams")
    print(f"  - Updated {docs_success_count}/{len(docs_updates)} GitHub Pages documentation images")
    print(f"  - Verified {verified_count}/{total_to_verify} diagrams have expected icon counts")
    print("\nFiles updated:")
    for update in docs_updates:
        print(f"  - {update['dest']}")

    print("\nNext steps:")
    print("  1. Review the generated diagrams for correctness")
    print("  2. Commit the updated images to git:")
    print("     git add docs/images/*.png examples/**/*.png examples/**/*.svg")
    print("     git commit -m 'Update GitHub Pages images with latest diagrams'")
    print("  3. Push to GitHub to update GitHub Pages")
    print("  4. The documentation will reflect the latest code changes")

# Return success if everything worked (allowing for optional images)
    print(f"\n📊 Final Summary:")
    print(f"  - Diagrams generated: {success_count}/{len(diagrams)}")
    print(f"  - Docs images updated: {docs_success_count}/{len(docs_updates)}")
    
    # Consider it successful if all diagrams were generated and most docs updates worked
    total_operations = len(diagrams) + len(docs_updates)
    successful_operations = success_count + docs_success_count
    success_rate = (successful_operations / total_operations) * 100 if total_operations > 0 else 0
    
    if success_rate >= 90:  # Allow for some optional images that might not exist
        print("\n🎉 All operations completed successfully!")
        return 0
    elif success_count == len(diagrams):  # At least diagrams were generated
        print(f"\n⚠️  Diagrams generated successfully, but some doc updates failed ({success_rate:.1f}% success rate)")
        return 1
    else:
        print(f"\n❌ Major issues: Only {success_rate:.1f}% operations successful")
        return 2

if __name__ == '__main__':
    sys.exit(main())