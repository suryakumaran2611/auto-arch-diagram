# Examples

This folder contains sample Infrastructure-as-Code (IaC) projects used to demonstrate diagram generation.

- `examples/terraform/*` are Terraform-only scenarios (parsed in static mode).
- `examples/serverless-website/*` are “secure serverless website” reference implementations across providers and IaC tools.

Notes:
- The generator’s static parsers currently support Terraform and CloudFormation, plus best-effort support for Azure Bicep and Pulumi YAML.
- Icon-rendered PNG/SVG/JPEG diagrams are best for Terraform examples (provider icon mapping is currently Terraform-centric).
