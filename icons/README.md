# Custom Cloud Provider Icons

This directory contains official cloud provider icons for services not yet available in the `diagrams` library.

## Directory Structure

```
icons/
├── aws/          # AWS service icons
├── azure/        # Azure service icons
├── gcp/          # Google Cloud Platform icons
└── README.md     # This file
```

## Icon Naming Convention

Icons should be named using the Terraform resource type pattern (without provider prefix):

- **AWS**: `{service}_{resource}.png` (e.g., `amplify_app.png`, `app_runner_service.png`)
- **Azure**: `{service}_{resource}.png` (e.g., `static_web_app.png`, `container_app.png`)
- **GCP**: `{service}_{resource}.png` (e.g., `cloud_run_service.png`)

## Icon Requirements

- **Format**: PNG with transparent background
- **Size**: 256x256 pixels (will be scaled to fit diagram nodes)
- **Color**: Official service icon colors from provider
- **Source**: Official architecture icon sets from:
  - AWS: https://aws.amazon.com/architecture/icons/
  - Azure: https://learn.microsoft.com/en-us/azure/architecture/icons/
  - GCP: https://cloud.google.com/icons

## Usage

The diagram generator automatically checks for custom icons before falling back to the diagrams library:

1. Custom icons in `icons/{provider}/` directory
2. Diagrams library built-in icons
3. Generic fallback icons (compute, storage, network, etc.)

## Icon Repository Status

**Current Icons Available:**
- **AWS:** 1,489 icons (official AWS Architecture Icons)
- **Azure:** 630 icons (Azure Public Service Icons V23)
- **GCP:** 23 icons (Google Cloud icons)
- **Total:** 2,142+ cloud service icons

All icons are converted to 256x256 PNG format with transparency, ready for use with the diagram generator.

## Automated Icon Processing

Icons have been downloaded from official sources and processed using ImageMagick:

```bash
# Process downloaded icon packages
cd icons
unzip aws-icons.zip -d .temp/aws
unzip Azure_Public_Service_Icons_V23.zip -d .temp/azure
unzip gcp.zip -d .temp/gcp

# Convert all SVG to PNG and normalize to 256x256
# (Script provided in tools/download_icons.sh)
```

**Key Features:**
- SVG to PNG conversion for all providers
- Automatic resizing to 256×256 pixels
- Transparent backgrounds preserved
- Filename normalization (lowercase, underscores)

## Manual Icon Addition

1. Download the official icon from the provider's architecture site
2. Ensure it's 256x256 PNG with transparent background
3. Name it according to the convention above
4. Place it in the appropriate provider directory
5. Test by regenerating diagrams that use the service

## License & Attribution

Icons are property of their respective cloud providers:
- AWS icons: © Amazon Web Services
- Azure icons: © Microsoft Corporation
- GCP icons: © Google LLC

These icons are used for architectural diagram generation only and remain the intellectual property of their respective owners. This repository does not claim any ownership over these icons.

## Examples

### AWS Services (Ready to Use)
- `app_runner_service.png` - AWS App Runner (azurerm_app_runner_service)
- `amplify_app.png` - AWS Amplify (aws_amplify_app)
- `arch_amazon_lightsail.png` - Amazon Lightsail

### Azure Services (Ready to Use)
- `static_web_app.png` - Azure Static Web Apps (azurerm_static_web_app)
- `container_app.png` - Azure Container Apps (azurerm_container_app)
- `02989_icon_service_container_apps_environments.png` - Container App Environments

### GCP Services (Ready to Use)
- `cloud_run_service.png` - Cloud Run Services (google_cloud_run_service)
- `cloud_run_v2_service.png` - Cloud Run v2 (google_cloud_run_v2_service)
- `vertexai_512_color.png` - Vertex AI

**Note:** Many icons retain their original naming from cloud providers. To use them with Terraform resource types, copy and rename them following the convention: remove provider prefix and use underscores.

Example:
```bash
# AWS App Runner: aws_app_runner_service → app_runner_service.png
cp aws/arch_aws_app_runner.png aws/app_runner_service.png

# Azure Static Web App: azurerm_static_web_app → static_web_app.png
cp azure/01007_icon_service_static_apps.png azure/static_web_app.png
```

## Maintenance

Review and update icons quarterly to ensure they match the latest official iconsets from cloud providers.
