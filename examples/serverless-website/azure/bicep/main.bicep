@description('Secure serverless website (Azure) - Storage + CDN (example)')
param location string = resourceGroup().location

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroup().name
  location: location
}

// Storage account with secure defaults (encryption, TLS). Static website hosting is optional.
resource stg 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'autoweb${uniqueString(resourceGroup().id)}'
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        blob: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// CDN profile + endpoint (simplified). For stronger security, consider Front Door Premium + WAF.
resource cdnProfile 'Microsoft.Cdn/profiles@2021-06-01' = {
  name: 'autoarch-cdn'
  location: 'global'
  sku: {
    name: 'Standard_Microsoft'
  }
}

resource cdnEndpoint 'Microsoft.Cdn/profiles/endpoints@2021-06-01' = {
  name: '${cdnProfile.name}/autoarch-endpoint'
  location: 'global'
  properties: {
    isHttpAllowed: false
    isHttpsAllowed: true
    origins: [
      {
        name: 'origin1'
        properties: {
          hostName: '${stg.name}.blob.core.windows.net'
          httpPort: 80
          httpsPort: 443
        }
      }
    ]
  }
  dependsOn: [
    stg
  ]
}
