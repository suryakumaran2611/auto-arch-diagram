<!-- auto-arch-diagram -->

## Architecture Diagram (Auto)

Summary: Generated a dependency-oriented CloudFormation diagram from changed resources.

```mermaid
flowchart AUTO
subgraph CloudFront[CloudFront]
  cfn_CloudFrontOAC["CloudFrontOAC\nAWS::CloudFront::OriginAccessControl"]
  cfn_Distribution["Distribution\nAWS::CloudFront::Distribution"]
end
subgraph S3[S3]
  cfn_LogsBucket["LogsBucket\nAWS::S3::Bucket"]
  cfn_SiteBucket["SiteBucket\nAWS::S3::Bucket"]
  cfn_SiteBucketPublicAccessBlock["SiteBucketPublicAccessBlock\nAWS::S3::BucketPublicAccessBlock"]
end
subgraph WAFv2[WAFv2]
  cfn_WafAcl["WafAcl\nAWS::WAFv2::WebACL"]
end
cfn_CloudFrontOAC --> cfn_Distribution
cfn_LogsBucket --> cfn_Distribution
cfn_LogsBucket --> cfn_SiteBucket
cfn_SiteBucket --> cfn_Distribution
cfn_SiteBucket --> cfn_SiteBucketPublicAccessBlock
cfn_WafAcl --> cfn_Distribution
```

Assumptions: Connections represent inferred references via Ref/GetAtt/Sub and DependsOn.

Rendered diagram: available as workflow artifact
