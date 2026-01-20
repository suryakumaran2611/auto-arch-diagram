import requests
import json

def get_public_cloud_icons():
    # We query the 'diagrams' repo file structure to find what icons are available
    repo_url = "https://api.github.com/repos/mingrammer/diagrams/git/trees/master?recursive=1"
    response = requests.get(repo_url).json()
    
    catalog = {"aws": [], "azure": [], "gcp": []}
    
    base_raw_url = "https://raw.githubusercontent.com/mingrammer/diagrams/master/"

    for item in response.get("tree", []):
        path = item["path"]
        # Look for PNG files in the resource folders
        if path.startswith("resources/") and path.endswith(".png"):
            parts = path.split("/")
            provider = parts[1] # e.g., 'aws'
            
            if provider in catalog:
                service_name = parts[-1].replace(".png", "")
                catalog[provider].append({
                    "name": service_name,
                    "icon_url": base_raw_url + path
                })
                
    return catalog

# Save to JSON
if __name__ == "__main__":
    cloud_data = get_public_cloud_icons()
    with open("public_cloud_catalog.json", "w") as f:
        json.dump(cloud_data, f, indent=4)
    print(f"Found {len(cloud_data['aws'])} AWS icons and {len(cloud_data['gcp'])} GCP icons!")
