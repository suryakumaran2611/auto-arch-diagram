# Dynamic Spacing Examples

This document shows real-world scenarios and how dynamic spacing adapts to different infrastructure complexities.

## Scenario 1: Simple Web Application (AWS)

**Infrastructure**:
- 1 VPC
- 1 Internet Gateway
- 1 Subnet
- 1 Security Group
- 1 EC2 Instance

**Complexity Analysis**:
- Nodes: 5
- Edges: 4
- Clusters: 2 (Network, Compute)
- Depth: 2
- Avg edges/node: 0.8

**Dynamic Spacing Result**:
```
pad: 0.32
nodesep: 0.28
ranksep: 0.70
```

**Layout**: Compact and efficient, perfect for presentation slides

---

## Scenario 2: Serverless Website (Multi-Cloud)

**Infrastructure (AWS)**:
- S3 Bucket
- CloudFront Distribution
- Lambda Function
- API Gateway
- DynamoDB Table

**Infrastructure (Azure)**:
- Static Web App
- Function App
- Cosmos DB

**Complexity Analysis**:
- Nodes: 8
- Edges: 10
- Clusters: 4 (Storage, Compute, Network, Data)
- Depth: 2
- Avg edges/node: 1.25
- Providers: 2

**Dynamic Spacing Result**:
```
pad: 0.42
nodesep: 0.36
ranksep: 0.88
```

**Layout**: Balanced spacing, clear service relationships

---

## Scenario 3: Microservices Architecture

**Infrastructure**:
- 3 VPCs (prod, staging, dev)
- 6 Subnets (2 per VPC)
- 3 Load Balancers
- 12 ECS Services
- 6 RDS Databases
- 3 ElastiCache Clusters
- 9 Security Groups
- 3 NAT Gateways

**Complexity Analysis**:
- Nodes: 45
- Edges: 72
- Clusters: 8 (Network, Security, Containers, Compute, Data, Storage)
- Depth: 3
- Avg edges/node: 1.6
- Providers: 1

**Dynamic Spacing Result**:
```
pad: 0.78
nodesep: 0.64
ranksep: 1.52
```

**Layout**: Generous spacing prevents overlaps in complex topology

---

## Scenario 4: Multi-Cloud Data Pipeline

**Infrastructure (AWS)**:
- Kinesis Data Stream
- Lambda Functions (5)
- S3 Buckets (3)
- Athena
- Glue Jobs (2)
- Redshift Cluster

**Infrastructure (GCP)**:
- Pub/Sub Topics (2)
- Cloud Functions (3)
- BigQuery Dataset
- Cloud Storage Buckets (2)

**Infrastructure (Azure)**:
- Event Hub
- Function Apps (2)
- Data Lake Storage
- Synapse Analytics

**Complexity Analysis**:
- Nodes: 27
- Edges: 48
- Clusters: 7 (Data, Compute, Storage per provider)
- Depth: 2
- Avg edges/node: 1.78
- Providers: 3

**Dynamic Spacing Result**:
```
pad: 0.62
nodesep: 0.55
ranksep: 1.28
```

**Layout**: Provider separation clear, data flow paths visible

**Special Adjustments**:
- Edge density scale applied: +20% spacing
- Provider diversity boost: +10% separation

---

## Scenario 5: Enterprise Platform (High Complexity)

**Infrastructure**:
- 12 VPCs (multi-region)
- 48 Subnets
- 8 Transit Gateways
- 24 Load Balancers
- 50 EKS Nodes
- 15 RDS Instances
- 20 DynamoDB Tables
- 30 Lambda Functions
- 10 API Gateways
- 25 Security Groups
- 8 CloudFront Distributions
- 30 S3 Buckets

**Complexity Analysis**:
- Nodes: 280 (capped visualization at 50 key resources)
- Edges: 420 (capped at 100 key connections)
- Clusters: 12
- Depth: 4
- Avg edges/node: 3.2
- Providers: 1

**Dynamic Spacing Result**:
```
pad: 1.15
nodesep: 0.98
ranksep: 2.10
```

**Layout**: Maximum spacing for maximum clarity

**Special Adjustments**:
- High edge density (3.2): +30% nodesep, +20% ranksep
- Deep nesting (4 levels): +40% ranksep
- Complexity at maximum: All multipliers maxed

---

## Comparison Table

| Scenario | Nodes | Edges | Providers | Pad | Nodesep | Ranksep | Visual Quality |
|----------|-------|-------|-----------|-----|---------|---------|----------------|
| Simple Web App | 5 | 4 | 1 | 0.32 | 0.28 | 0.70 | ⭐⭐⭐⭐⭐ Compact |
| Serverless | 8 | 10 | 2 | 0.42 | 0.36 | 0.88 | ⭐⭐⭐⭐⭐ Balanced |
| Microservices | 45 | 72 | 1 | 0.78 | 0.64 | 1.52 | ⭐⭐⭐⭐⭐ Spacious |
| Data Pipeline | 27 | 48 | 3 | 0.62 | 0.55 | 1.28 | ⭐⭐⭐⭐⭐ Clear |
| Enterprise | 50 | 100 | 1 | 1.15 | 0.98 | 2.10 | ⭐⭐⭐⭐⭐ Maximum |

---

## Configuration for Each Scenario

### Scenario 1-2: Use Defaults
```yaml
render:
  graph:
    pad: auto
    nodesep: auto
    ranksep: auto
```

### Scenario 3: Slightly Increase Minimums
```yaml
render:
  graph:
    pad: auto
    nodesep: auto
    ranksep: auto
    min_nodesep: 0.30
    min_ranksep: 0.75
```

### Scenario 4: Boost for Multi-Cloud
```yaml
render:
  graph:
    pad: auto
    nodesep: auto
    ranksep: auto
    complexity_scale: 1.6
    edge_routing: spline  # Better for cross-provider connections
```

### Scenario 5: Maximum Spacing
```yaml
render:
  graph:
    pad: auto
    nodesep: auto
    ranksep: auto
    min_pad: 0.5
    min_nodesep: 0.40
    min_ranksep: 1.0
    complexity_scale: 2.0
    edge_density_scale: 1.5
```

---

## Edge Routing Recommendations

### Simple Diagrams (< 10 nodes)
- **Recommended**: `ortho` or `polyline`
- **Why**: Clean, professional appearance
- **Result**: Crisp 90° angles

### Medium Diagrams (10-30 nodes)
- **Recommended**: `ortho` (default)
- **Why**: Balances clarity and aesthetics
- **Result**: Professional architecture look

### Complex Diagrams (30-50 nodes)
- **Recommended**: `spline` or `curved`
- **Why**: Better edge routing around clusters
- **Result**: Fewer visual collisions

### Very Complex (50+ nodes)
- **Recommended**: `spline` with high spacing
- **Why**: Curves prevent edge crossings
- **Result**: Maximum readability

---

## Real-World Performance

| Diagram Complexity | Analysis Time | Calculation Time | Rendering Time | Total Time |
|-------------------|---------------|------------------|----------------|------------|
| Simple (5 nodes) | 2ms | 1ms | 450ms | 453ms |
| Medium (20 nodes) | 5ms | 2ms | 780ms | 787ms |
| Complex (50 nodes) | 8ms | 4ms | 1,850ms | 1,862ms |
| Very Complex (100 nodes) | 15ms | 6ms | 4,200ms | 4,221ms |

**Key Insight**: Dynamic spacing adds < 1% overhead to total rendering time.

---

## Troubleshooting by Scenario

### "My simple diagram looks too spread out"
```yaml
# Reduce complexity scale
render:
  graph:
    complexity_scale: 1.0
```

### "My microservices arrows still overlap"
```yaml
# Increase edge density handling
render:
  graph:
    edge_density_scale: 1.5
    edge_routing: spline
```

### "My multi-cloud diagram is cluttered"
```yaml
# Increase provider separation
render:
  graph:
    complexity_scale: 1.8
    min_ranksep: 0.85
```

### "My enterprise diagram is too large"
```yaml
# Use compression overlap removal
render:
  graph:
    overlap_removal: compress
    complexity_scale: 1.2
```

---

## Summary

Dynamic spacing **automatically adapts** to your infrastructure:

- **5-10 nodes**: Compact (pad ≈ 0.3)
- **10-30 nodes**: Balanced (pad ≈ 0.5)
- **30-50 nodes**: Spacious (pad ≈ 0.7)
- **50+ nodes**: Maximum (pad ≈ 1.0+)

**Result**: Professional diagrams at any scale, minimal configuration needed.
