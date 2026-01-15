# Architecture Diagram Examples

This directory contains comprehensive examples demonstrating the full capabilities of auto-arch-diagram, from simple serverless architectures to complex event-driven data pipelines with custom icons.

## 🎯 Featured Example: Custom Icons Demo

**[terraform/custom-icons-demo/](terraform/custom-icons-demo/)** - Complex serverless data pipeline (40+ resources)

### What It Demonstrates

✅ **Custom Icon Support** - 11 specialized icons for domain-specific components  
✅ **VPC Grouping** - Resources organized within VPC with public/private subnet distinction  
✅ **Event-Driven Architecture** - API Gateway → Lambda → Kinesis → ElasticSearch workflow  
✅ **Multiple Data Stores** - S3, DynamoDB, ElasticSearch, Glue Catalog integration  
✅ **Serverless Patterns** - Lambda, Step Functions, EventBridge, SNS/SQS  
✅ **Professional Styling** - White backgrounds, colored borders, center-based edge routing  
✅ **Complex Topology** - Intelligent AUTO layout with no overlaps

**Generated Files:**
- PNG: 589 KB - High-quality raster
- SVG: 827 KB - Vector with embedded base64 icons
- JPEG: 983 KB - Compressed format
- Mermaid: Inline flowchart diagram
- Markdown: Architecture documentation

## 📁 All Examples

### Terraform Examples

#### terraform/custom-icons-demo/ ⭐
**Complex serverless data pipeline** demonstrating all tool capabilities
- 40+ resources with 11 custom icons
- VPC with public/private subnets
- Event-driven architecture (Kinesis, Lambda, EventBridge)
- Data pipeline (S3, Glue, Athena, ElasticSearch)
- Monitoring and alerting (CloudWatch, SNS, SQS)

#### serverless-website/*/terraform/
**Multi-cloud serverless static website hosting**
- aws/ - S3 + CloudFront + ACM
- azure/ - Storage Account + CDN
- gcp/ - Cloud Storage + Cloud CDN
- ibm/ - Cloud Object Storage
- oci/ - Object Storage

### CloudFormation Examples

#### serverless-website/aws/cloudformation/
**AWS serverless architecture** using CloudFormation YAML

### Bicep Examples

#### serverless-website/azure/bicep/
**Azure serverless architecture** using Bicep

### Pulumi Examples

#### serverless-website/*/pulumi/
**Cross-platform Pulumi YAML** examples

## 🎨 Custom Icon Support

See the `custom-icons-demo` example for custom icon integration:

1. **Create Icons**: Place PNG files in [../icons/custom/](../icons/custom/) (64x64+ recommended)
2. **Tag Resources**: Add `Icon = "custom://iconname"` tag to Terraform resources
3. **Auto-Detection**: Tool automatically uses custom icons for tagged resources

**11 Custom Icons Included:** DataPipeline, DataStream, StreamProcessor, EventTrigger, DatabaseStream, SearchEngine, DataCrawler, Scheduler, AlertNotification, MessageQueue, CloudMonitor

See [../icons/custom/README.md](../icons/custom/README.md) for details.

## 🚀 Generating Examples

### Regenerate All Examples

```bash
# From repository root
python tools/regenerate_examples.py
```

### Generate Single Example

```bash
python tools/generate_arch_diagram.py \
  --changed-files examples/terraform/custom-icons-demo/main.tf \
  --direction AUTO \
  --out-md examples/terraform/custom-icons-demo/architecture-diagram.md \
  --out-png examples/terraform/custom-icons-demo/architecture-diagram.png \
  --out-svg examples/terraform/custom-icons-demo/architecture-diagram.svg
```

## 📊 Complexity Comparison

| Example | Resources | VPCs | Subnets | Custom Icons | Edges | Lines |
|---------|-----------|------|---------|--------------|-------|-------|
| custom-icons-demo | 40 | 1 | 2 | 11 | 35+ | 530 |
| serverless/aws/tf | 8 | 0 | 0 | 0 | 5 | 120 |
| serverless/azure/tf | 7 | 0 | 0 | 0 | 4 | 110 |
| serverless/gcp/tf | 6 | 0 | 0 | 0 | 4 | 100 |

## 🏗️ Architecture Patterns

### Event-Driven Architecture
API Gateway triggers, S3 events, DynamoDB streams, EventBridge scheduling

### Data Processing Pipelines
Real-time streaming (Kinesis), batch processing (Lambda), cataloging (Glue), analytics (Athena)

### Serverless Best Practices
VPC configuration, dead letter queues, CloudWatch monitoring, Step Functions orchestration

## 💡 Tips

- Use `AUTO` direction for intelligent layout selection
- Add `Name` tags for better node labels
- Use `Tier = "public"/"private"` tags for subnet classification  
- Create custom icons for domain-specific components
- Keep examples under 50 resources for optimal rendering

## 📝 Technical Notes

- Static parsers support Terraform, CloudFormation, Bicep, Pulumi YAML
- Icon-rendered PNG/SVG/JPEG diagrams are best for Terraform (2,100+ official icons)
- Provider icon mapping: AWS, Azure, GCP, IBM Cloud, Oracle Cloud
- VPC grouping automatically detects network hierarchy
