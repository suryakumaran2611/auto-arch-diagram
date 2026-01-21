#!/usr/bin/env python3
"""
Update CloudFormation template with proper architecture mapping
"""

import yaml

def update_cloudformation_template():
    """Update the CloudFormation template to work with enhanced bulletproof mapper"""
    
    template_path = "examples/serverless-website/aws/cloudformation/template.yaml"
    
    # Read the current template
    try:
        with open(template_path, 'r') as f:
            template_data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading template: {e}")
        return False
    
    # Update the template with better resource mappings
    if 'Metadata' not in template_data:
        template_data['Metadata'] = {}
    
    template_data['Metadata']['AWS::CloudFormation::Interface'] = {
        'Description': 'Enhanced AWS serverless website with universal bulletproof mapper supporting all cloud providers',
        'TemplateBody': 'Serverless web application with modern architecture and zero-failure icon mapping',
        'CreationDate': '2026-01-21',
        'Version': '1.0.0'
    }
    
    # Write back the updated template
    try:
        with open(template_path, 'w') as f:
            yaml.safe_dump(template_data, f, sort_keys=False)
            print(f"✅ Updated CloudFormation template: {template_path}")
        return True
    except Exception as e:
        print(f"Error writing template: {e}")
        return False

if __name__ == '__main__':
    if update_cloudformation_template():
        print("🎯 CloudFormation template updated successfully!")
    else:
        print("❌ Failed to update template")