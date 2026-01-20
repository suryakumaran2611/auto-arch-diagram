import json
import os
import boto3
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from google.cloud import billing_v1
import diagrams
from pathlib import Path

def get_icon_path(provider, service_name):
    base_path = Path(diagrams.__file__).parent / provider
    for path in base_path.rglob("*.png"):
        if service_name.lower() in path.name.lower():
            return str(path)
    return None

def get_aws_data():
    print("Fetching AWS services & icons...")
    ssm = boto3.client('ssm', region_name='us-east-1')
    data = []
    paginator = ssm.get_paginator('get_parameters_by_path')
    for page in paginator.paginate(Path='/aws/service/global-infrastructure/services'):
        for param in page['Parameters']:
            name = param['Name'].split('/')[-1]
            data.append({
                "name": name,
                "icon_local_path": get_icon_path("aws", name)
            })
    return data

def get_azure_data(subscription_id):
    print("Fetching Azure services & icons...")
    try:
        credential = DefaultAzureCredential()
        client = ResourceManagementClient(credential, subscription_id)
        data = []
        for provider in client.providers.list():
            ns = provider.namespace
            data.append({
                "name": ns,
                "icon_local_path": get_icon_path("azure", ns)
            })
        return data
    except Exception as e:
        print(f"Azure error: {e}")
        return []

def get_gcp_data():
    print("Fetching GCP services & icons...")
    try:
        client = billing_v1.CloudBillingClient()
        data = []
        for service in client.list_services():
            name = service.display_name
            icon_path = get_icon_path("gcp", name.replace(" ", ""))
            data.append({
                "name": name,
                "icon_local_path": icon_path
            })
        return data
    except Exception as e:
        print(f"GCP error: {e}")
        return []

def main():
    # Set your Azure subscription ID here
    azure_subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID", "SUBSCRIPTION_ID_HERE")
    combined_data = {
        "aws": get_aws_data(),
        "azure": get_azure_data(azure_subscription_id),
        "gcp": get_gcp_data()
    }
    with open("cloud_catalog.json", "w") as f:
        json.dump(combined_data, f, indent=4)
    print("Done! Check cloud_catalog.json")

if __name__ == "__main__":
    main()
