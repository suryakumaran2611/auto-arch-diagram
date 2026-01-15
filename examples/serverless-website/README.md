# Secure Serverless Website examples

Goal: provide copy/pasteable IaC reference implementations for a static “serverless website” with a security-first posture.

Common security controls shown (where the provider supports it):

- TLS/HTTPS enforced at the edge
- WAF / request filtering
- Origin is private where possible (preferred: CDN-to-origin auth)
- Encryption at rest
- Logging enabled (bucket/CDN/WAF)
- Versioning enabled for storage

Structure:

- `aws/terraform`, `aws/cloudformation`, `aws/pulumi`, `aws/cdk`
- `azure/terraform`, `azure/bicep`, `azure/pulumi`
- `gcp/terraform`, `gcp/pulumi`
- `oci/terraform`, `oci/pulumi`
- `ibm/terraform`, `ibm/pulumi`

Notes:
- Some examples are intentionally “diagram-friendly” and may require additional parameters to deploy.
- Terraform examples currently produce the best icon-rendered diagrams.
