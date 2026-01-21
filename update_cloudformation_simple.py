#!/usr/bin/env python3
"""
Simple CloudFormation template update
"""

import os

def update_template():
    """Update CloudFormation template description"""
    template_path = "examples/serverless-website/aws/cloudformation/template.yaml"
    
    # Update the description
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Update the description line
        updated_content = content.replace(
            "Description: 'Secure serverless website (AWS) - S3 private origin + CloudFront + WAF + monitoring'",
            "Description: 'Secure serverless website (AWS) with enhanced universal bulletproof mapper supporting all cloud providers'"
        )
        
        with open(template_path, 'w') as f:
            f.write(updated_content)
            print(f"✅ Updated CloudFormation template description: {template_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to update template: {e}")
        return False

if __name__ == '__main__':
    if update_template():
        print("✅ CloudFormation template updated successfully!")
    else:
        print("❌ Failed to update template")