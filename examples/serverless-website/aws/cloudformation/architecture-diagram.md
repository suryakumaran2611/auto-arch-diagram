<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented CloudFormation diagram from changed resources.

```mermaid
flowchart LR
subgraph Network[Network]
  cfn_CloudFrontOAC["CloudFrontOAC\nOriginAccessControl"]
  cfn_Distribution["Distribution\nDistribution"]
end
subgraph Security[Security]
  cfn_WafAcl["WafAcl\nWebACL"]
end
subgraph Storage[Storage]
  cfn_LogsBucket["LogsBucket\nBucket"]
  cfn_SiteBucket["SiteBucket\nBucket"]
  cfn_SiteBucketPublicAccessBlock["SiteBucketPublicAccessBlock\nBucketPublicAccessBlock"]
end
cfn_CloudFrontOAC --> cfn_Distribution
cfn_LogsBucket --> cfn_Distribution
cfn_LogsBucket --> cfn_SiteBucket
cfn_SiteBucket --> cfn_Distribution
cfn_SiteBucket --> cfn_SiteBucketPublicAccessBlock
cfn_WafAcl --> cfn_Distribution
```

Assumptions: Connections represent inferred references via Ref/GetAtt/Sub and DependsOn.

Rendered diagram: not available (icons require Graphviz + diagrams)
