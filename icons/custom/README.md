# Custom Icons

This directory contains custom icons that can be used in your architecture diagrams. The tool supports custom icons by referencing them with the `Icon` tag in your Terraform resources.

## Usage

To use a custom icon, add an `Icon` tag to your resource:

```hcl
resource "aws_lambda_function" "my_function" {
  # ... other configuration ...
  
  tags = {
    Name = "my-function"
    Icon = "custom://datapipeline"  # References icons/custom/datapipeline.png
  }
}
```

## Icon Format Requirements

- **Format**: PNG with transparency (recommended)
- **Size**: 64x64 pixels or larger (will be auto-scaled)
- **Naming**: Use lowercase with no spaces (e.g., `datapipeline.png`, `searchengine.png`)
- **Color**: Professional colors that match your brand or architecture style

## Custom Icons in This Directory

### datapipeline.png
A pipeline icon representing data ingestion and processing workflows.

### datastream.png
A stream icon for real-time data streaming services.

### streamprocessor.png
A processor icon for stream processing functions.

### eventtrigger.png
An event trigger icon for event-driven architectures.

### databasestream.png
A database stream icon for CDC (Change Data Capture) patterns.

### searchengine.png
A search engine icon for search and analytics services.

### datacrawler.png
A crawler icon for data discovery and cataloging.

### scheduler.png
A scheduler icon for scheduled/batch processing.

### alertnotification.png
An alert icon for notification and alerting systems.

### messagequeue.png
A message queue icon for async messaging patterns.

### cloudmonitor.png
A monitoring icon for observability and metrics.

## Creating Your Own Icons

1. Design your icon as a PNG with transparent background
2. Save it as 64x64 or 128x128 pixels
3. Use professional, consistent colors
4. Place it in the `icons/custom/` directory
5. Reference it in Terraform: `Icon = "custom://youricon"`

## Icon Design Guidelines

- **Simplicity**: Keep icons simple and recognizable at small sizes
- **Consistency**: Use consistent style across all custom icons
- **Contrast**: Ensure good contrast with white backgrounds
- **Professionalism**: Match enterprise architecture diagram standards
