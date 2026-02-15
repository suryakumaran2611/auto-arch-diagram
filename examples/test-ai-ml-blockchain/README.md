# AI/ML/Blockchain Service Testing Examples

This directory contains comprehensive test files for verifying that the Auto Architecture Diagram action properly recognizes and categorizes AI, ML, and Blockchain services across all major cloud providers.

## 🎯 Purpose

- **Service Mapping Validation**: Ensure all new services are properly categorized
- **Icon Recognition**: Verify cloud provider icons are correctly assigned
- **Layout Testing**: Test diagram generation with complex AI/ML architectures
- **Multi-Cloud Testing**: Validate cross-provider service recognition

## 📁 Directory Structure

```
test-ai-ml-blockchain/
├── aws/
│   ├── main.tf              # AWS AI/ML/Blockchain services
│   └── terraform/
├── azure/
│   ├── main.tf              # Azure AI/ML/Blockchain services
│   └── terraform/
├── gcp/
│   ├── main.tf              # GCP AI/ML services
│   └── terraform/
├── oracle/
│   ├── main.tf              # Oracle Cloud AI/ML services
│   └── terraform/
└── ibm/
    ├── main.tf              # IBM Cloud AI/ML/Blockchain services
    └── terraform/
```

## 🚀 Quick Testing

### Single Provider Test

```powershell
# Test AWS services only
python tools/generate_arch_diagram.py \
  --iac-root test-ai-ml-blockchain/aws \
  --direction AUTO \
  --out-md aws-test.md \
  --out-png aws-test.png

# Test Azure services only
python tools/generate_arch_diagram.py \
  --iac-root test-ai-ml-blockchain/azure \
  --direction LR \
  --out-md azure-test.md \
  --out-png azure-test.png
```

### Multi-Provider Test

```powershell
# Test all providers together
python tools/generate_arch_diagram.py \
  --iac-root test-ai-ml-blockchain \
  --direction AUTO \
  --out-md all-providers.md \
  --out-png all-providers.png \
  --out-svg all-providers.svg
```

### AI Mode Test

```powershell
# Enhanced analysis with AI mode
$env:AZURE_OPENAI_API_KEY = "your-key-here"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com"
$env:DEPLOYMENT_NAME = "gpt-4o"
python tools/generate_arch_diagram.py \
  --mode ai \
  --iac-root test-ai-ml-blockchain \
  --direction AUTO \
  --out-md ai-enhanced.md \
  --out-png ai-enhanced.png
```

## 🧪 Expected Results

When successful, diagrams should show:

### Service Categories
- **ML Services**: Categorized under 'ml' module (green/blue theme)
- **Blockchain Services**: Categorized under 'blockchain' module (purple theme)
- **AI Services**: Properly grouped with specialized icons

### Cloud Provider Icons
- **AWS**: Official AWS orange icons for SageMaker, Bedrock, QLDB
- **Azure**: Official Azure blue icons for Azure ML, Cognitive Services
- **GCP**: Official GCP green icons for Vertex AI, AutoML
- **Oracle**: Oracle Cloud purple icons for OCI AI Services
- **IBM**: IBM Cloud grey/blue icons for Watson services

### Layout Optimization
- **Intelligent Grouping**: AI/ML services grouped together
- **Network Separation**: Different providers clearly separated
- **Edge Types**: Different line styles for AI vs data connections
- **Cluster Organization**: Logical grouping of related services

## 🔧 Debugging

### Enable Debug Mode

```powershell
# Show detailed mapping information
$env:AUTO_ARCH_DEBUG = "1"
python tools/generate_arch_diagram.py --iac-root test-ai-ml-blockchain --out-md debug.md
```

Debug output shows:
- Service recognition details
- Provider detection logic
- Category assignment
- Icon mapping resolution

### Common Issues

**Service Not Recognized**
- Check service name spelling in Terraform files
- Verify service mapping in `service_map` dictionary
- Enable debug mode to see mapping process

**Wrong Icon Displayed**
- Verify icon files exist in `icons/` directory
- Check provider mapping in `icon_mapping`
- Ensure proper naming convention

**Incorrect Categorization**
- Review `service_map` entries
- Check category assignment logic
- Verify acronym handling

## 📊 Coverage Verification

### AWS Services (47 total)
- [x] SageMaker (Notebook, Endpoint, Model, Pipeline)
- [x] Bedrock (Agent, Knowledge Base, Runtime)
- [x] AI Services (Textract, Comprehend, Translate, Polly, Rekognition)
- [x] Custom AI (Personalize, Forecast, Lex, Transcribe)
- [x] Blockchain (Managed Blockchain, QLDB)
- [x] Integration Services (Amplify, AppSync)

### Azure Services (23 total)
- [x] Azure ML (Workspace, Compute, Model, Endpoint)
- [x] Azure OpenAI Service
- [x] Cognitive Services (Computer Vision, Face, Speech, Language)
- [x] Blockchain Service (Members, Nodes)
- [x] Integration (Databricks, Synapse)

### GCP Services (18 total)
- [x] Vertex AI (Notebooks, Endpoints, Models, Training)
- [x] AutoML (Tables, Vision, NLP, Translation)
- [x] Cloud AI APIs (Speech, Vision, Recommendations)
- [x] Integration (Datalab, Colab, Jupyter)

### Oracle Cloud Services (8 total)
- [x] OCI AI Services (Language, Vision, Data Science)
- [x] AI Anomaly Detection
- [x] Blockchain Platform

### IBM Cloud Services (8 total)
- [x] Watson (Studio, Machine Learning, AutoAI, Assistant, Discovery)
- [x] Analytics (Cloud Pak for Data, Cognos)
- [x] Blockchain Platform

## 🎯 Success Criteria

A successful test should demonstrate:

1. **Service Recognition**: All 104+ services properly identified
2. **Categorization**: Correct assignment to ML/Blockchain modules
3. **Icon Mapping**: Appropriate cloud provider icons displayed
4. **Layout Quality**: Professional, readable diagram organization
5. **Cross-Provider Support**: Multiple providers in single diagram
6. **AI Enhancement**: Improved analysis when AI mode is enabled

## 🐛 Troubleshooting

### Service Not Found
```bash
# Check if service exists in mapping
python -c "
import sys; sys.path.insert(0, 'tools')
from generate_arch_diagram import service_map
service = 'aws_sagemaker_xyz'
category = service_map.get(service.split('_')[1])
print(f'{service}: {category}')
"
```

### Icon Missing
```powershell
# Verify icon exists
ls icons/aws/ | grep sagemaker
ls icons/azure/ | grep -i machine
ls icons/gcp/ | grep -i vertex
```

### Generation Failures
```powershell
# Test with minimal example first
echo "resource \"aws_ec2_instance\" \"test\" {}" > minimal.tf
python tools/generate_arch_diagram.py --iac-root . --out-md minimal.md
```

## 📈 Performance Benchmarks

### Large Diagram Generation
- **< 50 resources**: Should complete in < 30 seconds
- **50-100 resources**: Should complete in < 60 seconds
- **100+ resources**: May take 1-2 minutes

### AI Mode Performance
- **Small diagrams**: Additional 5-10 seconds for AI analysis
- **Medium diagrams**: Additional 10-20 seconds for AI analysis
- **Large diagrams**: Additional 20-30 seconds for AI analysis

## 🔄 Continuous Testing

### Automated Validation

```yaml
# .github/workflows/test-services.yml
name: Test AI/ML/Blockchain Services

on:
  push:
    paths: ['test-ai-ml-blockchain/**']
  pull_request:
    paths: ['test-ai-ml-blockchain/**']
  workflow_dispatch:

jobs:
  test-services:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install python-hcl2 diagrams graphviz
      - name: Test AWS services
        run: |
          python tools/generate_arch_diagram.py \
            --iac-root test-ai-ml-blockchain/aws \
            --out-md aws-test.md \
            --out-png aws-test.png
      - name: Test Azure services
        run: |
          python tools/generate_arch_diagram.py \
            --iac-root test-ai-ml-blockchain/azure \
            --out-md azure-test.md \
            --out-png azure-test.png
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: test-diagrams
          path: |
            aws-test.*
            azure-test.*
```

This comprehensive test suite ensures all new AI, ML, and Blockchain services work correctly across all supported cloud providers.