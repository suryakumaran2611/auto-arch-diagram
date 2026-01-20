#!/usr/bin/env python3
"""
Download complete icon libraries from GitHub diagrams repository.
This fetches ALL PNG icons across providers without needing to know specific service names.
"""

import os
import requests
import json
from pathlib import Path


def download_all_cloud_icons():
    # We use the GitHub Trees API to see all files in diagrams repository
    # This avoids having to know every service name in advance
    repo_url = (
        "https://api.github.com/repos/mingrammer/diagrams/git/trees/master?recursive=1"
    )
    raw_base = "https://raw.githubusercontent.com/mingrammer/diagrams/master/"

    print("Fetching global service list from GitHub...")
    try:
        response = requests.get(repo_url).json()
    except Exception as e:
        print(f"Error connecting to GitHub: {e}")
        return

    # Providers we want to target
    targets = ["aws", "azure", "gcp"]
    stats = {t: 0 for t in targets}
    mapping = {t: [] for t in targets}

    for item in response.get("tree", []):
        path = item["path"]

        # Filter for PNG icons in provider folders
        # Path format: resources/aws/compute/ec2.png
        if path.startswith("resources/") and path.endswith(".png"):
            parts = path.split("/")
            if len(parts) < 4:
                continue

            provider = parts[1]
            if provider in targets:
                category = parts[2]
                service_name = parts[-1].replace(".png", "")
                download_url = raw_base + path

                # Create local folder structure
                local_dir = f"cloud_icons/{provider}/{category}"
                os.makedirs(local_dir, exist_ok=True)

                # Download the icon
                file_path = f"{local_dir}/{service_name}.png"
                if not os.path.exists(file_path):
                    img_data = requests.get(download_url).content
                    with open(file_path, "wb") as f:
                        f.write(img_data)

                mapping[provider].append(
                    {
                        "service": service_name,
                        "category": category,
                        "local_path": file_path,
                        "url": download_url,
                    }
                )
                stats[provider] += 1
                print(f"[{provider.upper()}] Downloaded: {service_name}", end="\r")

    # Save mapping to a JSON file for your app/tool to use
    with open("service_icon_mapping.json", "w") as f:
        json.dump(mapping, f, indent=4)

    print("\n\nDownload Complete!")
    for p, count in stats.items():
        print(f"- {p.upper()}: {count} icons saved.")


if __name__ == "__main__":
    download_all_cloud_icons()
