# TerraVision Mock Integration Guide

## Overview

The auto-arch-diagram project now includes comprehensive TerraVision integration with advanced mock capabilities, enabling **zero-credential** architecture analysis in CI/CD environments while maintaining enterprise-grade security.

## 🚀 Key Features

### **Comprehensive Mock Support**
- **Multi-Cloud**: AWS, Azure, GCP, OCI, IBM Cloud
- **Security Levels**: Development, Staging, Production profiles
- **Environment Types**: Dev, Test, Prod configurations
- **CI/CD Ready**: GitHub Actions, GitLab CI, Jenkins support

### **Enhanced Analysis Capabilities**
- **Dependency Mapping**: Advanced resource relationship detection
- **Complexity Scoring**: Automated architecture complexity analysis
- **Provider Detection**: Automatic multi-cloud provider identification
- **Metadata Extraction**: Rich metadata for enhanced diagram generation

## 🛡️ Security-First Design

### **Zero Real Credentials Required**
```bash
# All mock credentials - no real cloud access needed
AWS_ACCESS_KEY_ID=mock_access_key_dev
AWS_SECRET_ACCESS_KEY=mock_secret_key_dev
ARM_SUBSCRIPTION_ID=mock_subscription_id_dev
GOOGLE_PROJECT_ID=mock_project_dev
```

### **Isolated Analysis Environment**
- **Docker Containerization**: TerraVision runs in isolated environment
- **No Network Calls**: All cloud API calls are blocked
- **Temporary Files**: Mock configurations are auto-generated and cleaned up
- **Audit Trail**: Complete logging of analysis process

## 📋 Configuration Profiles

### **Development Profile**
```yaml
name: development
description: "Development environment with minimal security"
aws_region: "us-east-1"
azure_location: "eastus"
gcp_region: "us-central1"
security_level: "low"
environment: "development"
```

### **Staging Profile**
```yaml
name: staging
description: "Staging environment with moderate security"
aws_region: "us-west-2"
azure_location: "westus"
gcp_region: "us-west1"
security_level: "medium"
environment: "staging"
```

### **Production Profile**
```yaml
name: production
description: "Production environment with high security"
aws_region: "us-gov-west-1"
azure_location: "usgovvirginia"
gcp_region: "us-central1"
security_level: "high"
environment: "production"
```

### **Multi-Cloud Profile**
```yaml
name: multi-cloud
description: "Multi-cloud setup across different regions"
aws_region: "us-east-1"
azure_location: "westeurope"
gcp_region: "europe-west1"
oci_region: "eu-frankfurt-1"
ibm_region: "eu-de"
security_level: "high"
environment: "production"
```

## 🛠️ Usage Examples

### **1. Basic Enhanced Generation**
```bash
# Generate diagrams with TerraVision using mock credentials
python tools/generate_arch_diagram.py \
  examples/terraform/aws-basic/ \
  --enable-terravision \
  --out-drawio enhanced-architecture.drawio
```

### **2. Profile-Based Generation**
```bash
# Generate using specific profile
export PROFILE=staging
python tools/generate_arch_diagram.py \
  examples/terraform/multi-cloud/ \
  --enable-terravision \
  --out-drawio staging-architecture.drawio
```

### **3. Mock Configuration Generation**
```bash
# List available profiles
python tools/mock_config_generator.py --list-profiles

# Generate all profile configurations
python tools/mock_config_generator.py --generate-all --output-dir ./mock-configs

# Generate specific profile
python tools/mock_config_generator.py \
  --profile production \
  --output-dir ./prod-configs
```

### **4. Docker Compose Integration**
```bash
# Generate Docker Compose for enhanced analysis
python tools/mock_config_generator.py \
  --profile multi-cloud \
  --docker-only \
  --output-dir ./docker-setup

# Run TerraVision with Docker Compose
cd docker-setup
docker-compose --profile multi-cloud up terravision
```

## 🔄 CI/CD Integration

### **GitHub Actions Workflow**
The enhanced workflow includes:

#### **Automatic Profile Detection**
```yaml
# Uses development profile by default for security
env:
  PROFILE: ${{ github.event.inputs.profile || 'development' }}
  ENABLE_TERRAVISION: ${{ github.event.inputs.enable_terravision || 'true' }}
```

#### **Mock Environment Loading**
```yaml
- name: Load Mock Environment
  run: |
    # Load profile-specific mock credentials
    cat ./mock-configs/$PROFILE/github.env >> $GITHUB_ENV
```

#### **Enhanced Generation with Fallback**
```yaml
- name: Generate Architecture Diagrams
  run: |
    # Try TerraVision first
    python tools/generate_arch_diagram.py --enable-terravision
    
- name: Generate Diagrams without TerraVision (Fallback)
  if: failure()
  run: |
    # Fallback to standard parsing
    python tools/generate_arch_diagram.py
```

### **GitLab CI Integration**
```yaml
# .gitlab-ci.yml
generate-diagrams:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  
  before_script:
    - python tools/mock_config_generator.py --profile $CI_ENVIRONMENT
  
  script:
    - docker compose run --rm terravision
  
  artifacts:
    reports:
      - artifacts/
```

### **Jenkins Pipeline Integration**
```groovy
// Jenkinsfile
pipeline {
  agent any
  
  stages {
    stage('Generate Diagrams') {
      steps {
        sh 'python tools/mock_config_generator.py --profile ${ENVIRONMENT}'
        sh 'docker compose run --rm terravision'
        archiveArtifacts artifacts: true
      }
    }
  }
}
```

## 🔧 Advanced Configuration

### **Custom Mock Profiles**
Create custom profiles by extending the configuration:

```python
# custom_profile.py
from tools.mock_config_generator import MockConfigProfile

custom_profile = MockConfigProfile(
    name="custom-secure",
    description="Custom high-security environment",
    aws_region="ca-central-1",
    azure_location="canada",
    gcp_region="northamerica-northeast1",
    security_level="high",
    environment="production"
)
```

### **Environment Variable Overrides**
```bash
# Override specific mock values
export AWS_DEFAULT_REGION=eu-west-1
export TF_VAR_security_level=high
export TF_VAR_environment=production

# Run with overrides
python tools/generate_arch_diagram.py \
  --enable-terravision \
  --out-drawio custom-architecture.drawio
```

## 📊 Enhanced Output Features

### **TerraVision-Enhanced Mermaid**
```mermaid
graph TD
    %% Enhanced by TerraVision Analysis
    %% Complexity Score: 25
    %% Providers: aws, azure
    %% Analysis Source: terravision
    
    subgraph "Complexity Analysis"
        complexity["Score: 25"]
        providers["2 providers"]
        resources["15 resources"]
    end
    
    aws_instance["Web Server"]:::aws_instance["fill:#FF9900,stroke:#FF6600,color:#fff"]
    azurerm_linux_virtual_machine["Database"]:::azurerm_linux_virtual_machine["fill:#0078D4,stroke:#005A9E,color:#fff"]
    aws_instance --> azurerm_linux_virtual_machine
```

### **Enhanced Draw.io Templates**
- **Provider-Specific Styling**: AWS (orange), Azure (blue), GCP (red)
- **Professional Boundaries**: Nested containers with proper colors
- **Smart Stencil Resolution**: AI-Lite heuristic resource mapping
- **Orthogonal Routing**: Professional connector styling

### **Rich Metadata**
```json
{
  "resources": {...},
  "dependencies": [...],
  "metadata": {
    "source": "terravision",
    "complexity_score": 25,
    "cloud_providers": ["aws", "azure"],
    "resource_types": ["ec2", "rds", "s3"],
    "analysis_duration_ms": 1250,
    "security_level": "production"
  }
}
```

## 🔍 Troubleshooting

### **Common Issues and Solutions**

#### **Docker Not Available**
```bash
# Error: docker command not found
# Solution: Use HCL2 fallback
python tools/generate_arch_diagram.py \
  examples/terraform/ \
  --out-drawio architecture.drawio
# (TerraVision will be disabled automatically)
```

#### **TerraVision Container Fails**
```bash
# Error: TerraVision analysis failed
# Solution: Check mock configuration
python tools/mock_config_generator.py --profile development --terraform-only
# Apply generated providers.tf manually
```

#### **Memory Issues**
```bash
# Error: Container killed due to memory limit
# Solution: Increase Docker memory
docker run --memory=4g patrickchugh/terravision draw
```

#### **Network Timeout**
```bash
# Error: TerraVision timeout
# Solution: Extend timeout and use local fallback
python tools/generate_arch_diagram.py \
  --enable-terravision \
  --out-drawio architecture.drawio
# Falls back to HCL2 after 30 seconds
```

## 📈 Performance Optimization

### **Caching Strategy**
```bash
# Cache TerraVision analysis results
export TERRAVISION_CACHE_DIR=./.terravision-cache
python tools/generate_arch_diagram.py --enable-terravision
```

### **Parallel Processing**
```bash
# Process multiple directories in parallel
find examples -name "*.tf" -exec dirname {} \; | \
  xargs -P 4 -I {} sh -c '
    python tools/generate_arch_diagram.py \
      --enable-terravision \
      --out-drawio {}/architecture.drawio
  '
```

### **Resource Monitoring**
```bash
# Monitor TerraVision resource usage
docker stats --no-stream patrickchugh/terravision
```

## 🔒 Security Best Practices

### **Production Deployment**
```yaml
# Use production profile with enhanced security
env:
  PROFILE: production
  ENABLE_TERRAVISION: true
  TF_VAR_security_level: high
```

### **Secrets Management**
```yaml
# Never store real credentials in repository
# Use mock credentials for analysis
# Real credentials only needed for actual terraform apply
```

### **Audit Trail**
```bash
# Enable comprehensive logging
export TERRAVISION_DEBUG=true
export AUTO_ARCH_DEBUG=true
python tools/generate_arch_diagram.py --enable-terravision
```

## 🎯 Next Steps

### **Advanced Features**
1. **Real-time Analysis**: Streaming TerraVision results
2. **Custom Stencils**: User-defined icon mappings
3. **Integration APIs**: REST API for external tools
4. **Performance Dashboard**: Real-time metrics and monitoring

### **Community Contributions**
- **New Profiles**: Contribute environment-specific profiles
- **Provider Support**: Add new cloud providers
- **Enhanced Mappings**: Improve resource type detection
- **Performance**: Optimize analysis speed and accuracy

---

## 📞 Support

For issues with TerraVision mock integration:

1. **Check Logs**: Enable debug mode with `TERRAVISION_DEBUG=true`
2. **Verify Docker**: Ensure Docker is running and accessible
3. **Profile Validation**: Use `--list-profiles` to verify configurations
4. **Fallback Strategy**: System automatically falls back to HCL2 parsing

**Generated by auto-arch-diagram TerraVision Integration**  
**Enterprise-grade mock capabilities for secure CI/CD architecture analysis**
