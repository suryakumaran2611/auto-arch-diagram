# Auto Architecture Diagram Documentation

## 🚀 Enhanced TerraVision Integration (Latest Release)

The auto-arch-diagram project now includes **enterprise-grade TerraVision integration** with comprehensive mock capabilities, enabling **zero-credential** architecture analysis in CI/CD environments while maintaining production-grade security and accuracy.

### 🌟 Key Highlights

- **🚀 TerraVision Integration**: AI-powered HCL analysis with Docker containerization
- **🛡️ Enterprise Security**: Mock-based analysis with profile-based configurations  
- **🎨 Professional Draw.io**: Universal Smart Architect with heuristic resource resolution
- **☁️ Multi-Cloud Support**: AWS, Azure, GCP, OCI, IBM with 100+ services
- **🔄 Resilient Architecture**: Multiple fallback strategies for maximum uptime
- **📊 Performance Metrics**: Resource usage monitoring and timing analysis

## 📚 Documentation

### **Core Documentation**
- **[📖 User Guide](USER_GUIDE.md)** - Comprehensive usage guide with TerraVision integration
- **[🚀 TerraVision Guide](TERRAVISION_MOCK_INTEGRATION.md)** - Detailed TerraVision mock integration documentation
- **[🛠️ Update Scripts](UPDATE_GITHUB_PAGES_README.md)** - Scripts for maintaining documentation
- **[🧪 Testing Guide](TESTING.md)** - Testing procedures and quality assurance

### **Configuration & Integration**
- **[⚙️ Configuration Reference](docs/CONFIG_REFERENCE.md)** - Complete configuration options
- **[🔄 Workflow Examples](docs/WORKFLOW_EXAMPLES.md)** - CI/CD integration examples
- **[🔧 Advanced Usage](docs/ADVANCED_USAGE.md)** - Advanced configuration and customization
- **[📋 Best Practices](docs/BEST_PRACTICES.md)** - Production deployment guidelines

### **API & Technical**
- **[📡 Security Guide](docs/SECURITY_GUIDE.md)** - Security considerations and best practices
- **[🔌 Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[🏗️ Architecture](docs/ARCHITECTURE.md)** - System architecture and design decisions
- **[🤝 Contributing](CONTRIBUTING.md)** - Contribution guidelines and development setup

## 🎯 Features Overview

### **TerraVision-Enhanced Analysis**
- **AI-Powered Dependency Mapping**: Enhanced resource relationship detection
- **Complexity Scoring**: Automated architecture complexity analysis
- **Multi-Cloud Provider Detection**: Automatic provider identification
- **Mock Configuration Profiles**: Development, Staging, Production, Multi-Cloud
- **Docker Integration**: Containerized analysis with comprehensive environment setup

### **Professional Draw.io Generation**
- **UniversalSmartArchitect**: AI-Lite heuristic resource resolution
- **Dynamic Stencil Resolution**: Smart path construction with fallback handling
- **Multi-Provider Styling**: Provider-specific colors and boundary designs
- **Enhanced Connections**: Orthogonal routing with jump arcs

### **Enterprise Security & CI/CD**
- **Zero Credential Requirements**: No real cloud access needed for analysis
- **Profile-Based Security**: Environment-specific mock configurations
- **GitHub Actions Integration**: Enhanced workflow with profile selection and fallback
- **Security Scanning**: Automated dependency and code security analysis

## 🚀 Quick Start

### **1. TerraVision-Enhanced Generation**
```bash
# Generate diagrams with TerraVision using mock credentials
python tools/generate_arch_diagram.py \
  examples/terraform/aws-basic/ \
  --enable-terravision \
  --out-drawio enhanced-architecture.drawio
```

### **2. Profile-Based Configuration**
```bash
# Generate production profile with enhanced security
python tools/mock_config_generator.py \
  --profile production \
  --output-dir ./prod-configs

# Use profile in analysis
source ./prod-configs/production/github.env
python tools/generate_arch_diagram.py \
  examples/terraform/production/ \
  --enable-terravision \
  --out-drawio production-architecture.drawio
```

### **3. CI/CD Integration**
```yaml
# GitHub Actions with TerraVision
name: Enhanced Architecture Diagram Generation

on:
  workflow_dispatch:
    inputs:
      profile:
        description: 'Configuration profile to use'
        default: 'development'
        type: choice
        options:
          - development
          - staging
          - production
          - multi-cloud
      enable_terravision:
        type: boolean
        default: true

jobs:
  generate-diagrams:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate Mock Configuration
        run: |
          python tools/mock_config_generator.py --profile ${{ github.event.inputs.profile }}
      - name: Generate Enhanced Diagrams
        run: |
          python tools/generate_arch_diagram.py --enable-terravision --out-drawio architecture.drawio
```

## 📊 Comparison: TerraVision vs Standard

| Capability | TerraVision Enhanced | Standard Analysis |
|------------|-------------------|-------------------|
| **Dependency Analysis** | ✅ AI-powered deep analysis | ⚠️ Basic pattern matching |
| **Complexity Scoring** | ✅ Automated scoring algorithm | ❌ Not available |
| **Multi-Cloud Support** | ✅ All major providers | ⚠️ Limited to AWS/Azure/GCP |
| **Security Requirements** | ❌ No real credentials needed | ⚠️ May need some access |
| **Analysis Speed** | 🐢 Slower (comprehensive) | ⚡ Faster (basic) |
| **Accuracy** | 🎯 High (enterprise-grade) | 👥 Medium (standard) |
| **CI/CD Integration** | ✅ Docker-based with profiles | ⚠️ Basic environment setup |

## 🎨 Example Outputs

### **Enhanced Mermaid with TerraVision**
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

### **Professional Draw.io Templates**
- **Provider-Specific Styling**: AWS (orange), Azure (blue), GCP (red)
- **Smart Stencil Resolution**: AI-Lite heuristic resource mapping
- **Professional Boundaries**: Nested containers with proper colors
- **Enhanced Connections**: Orthogonal routing with jump arcs

### **Rich Metadata Analysis**
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

## 🔧 Configuration Options

### **TerraVision Configuration**
```bash
# Enable TerraVision analysis
--enable-terravision

# Use real credentials (if available)
--no-mock-credentials

# Output formats
--out-drawio architecture.drawio
--out-md architecture.md
--out-mmd architecture.mmd
--out-png architecture.png
--out-svg architecture.svg
```

### **Mock Profile Management**
```bash
# List available profiles
python tools/mock_config_generator.py --list-profiles

# Generate all configurations
python tools/mock_config_generator.py --generate-all

# Generate specific profile types
python tools/mock_config_generator.py --profile production --terraform-only
python tools/mock_config_generator.py --profile staging --github-only
python tools/mock_config_generator.py --profile multi-cloud --docker-only
```

## 🛡️ Security Best Practices

### **Production Deployment**
```yaml
# Use production profile with enhanced security
env:
  PROFILE: production
  ENABLE_TERRAVISION: true
  TF_VAR_security_level: high
  TF_VAR_environment: production
```

### **Mock Credential Management**
- **Never store real credentials** in repository
- **Use mock configurations** for all analysis
- **Profile-based security** for different environments
- **Audit trail logging** for all analysis activities

## 📈 Performance & Monitoring

### **Metrics Collection**
```bash
# Enable comprehensive monitoring
export TERRAVISION_DEBUG=true
export AUTO_ARCH_DEBUG=true

# Resource usage tracking
docker stats --no-stream patrickchugh/terravision
```

### **Caching Strategy**
```bash
# Enable TerraVision result caching
export TERRAVISION_CACHE_DIR=./.terravision-cache

# Parallel processing for large infrastructures
find examples -name "*.tf" -exec dirname {} \; | \
  xargs -P 4 -I {} sh -c '
    python tools/generate_arch_diagram.py \
      --enable-terravision \
      --out-drawio {}/architecture.drawio
  '
```

---

## 🎯 Getting Started

1. **[📖 Read the User Guide](USER_GUIDE.md)** - Complete usage instructions
2. **[🚀 Try TerraVision](TERRAVISION_MOCK_INTEGRATION.md)** - Enhanced analysis setup  
3. **[🧪 Run Tests](TESTING.md)** - Verify your setup
4. **[🤝 Contribute](CONTRIBUTING.md)** - Help improve the project

## 🔗 External Links

- **[🌐 Live Demo](https://suryakumaran2611.github.io/auto-arch-diagram/)** - Interactive examples
- **[📦 GitHub Repository](https://github.com/suryakumaran2611/auto-arch-diagram)** - Source code and issues
- **[📚 Documentation Portal](https://suryakumaran2611.github.io/auto-arch-diagram/docs/)** - Complete documentation
- **[🐳 Docker Hub](https://hub.docker.com/r/patrickchugh/terravision)** - TerraVision container

---

*Generated by auto-arch-diagram with TerraVision Integration*  
*Enterprise-grade mock capabilities for secure CI/CD architecture analysis*
