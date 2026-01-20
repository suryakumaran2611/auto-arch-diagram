import os
import requests
import json


def download_all_cloud_icons():
    # Use GitHub Trees API to fetch all PNG icons
    repo_url = (
        "https://api.github.com/repos/mingrammer/diagrams/git/trees/master?recursive=1"
    )
    raw_base = "https://raw.githubusercontent.com/mingrammer/diagrams/master/"

    print("Fetching complete icon libraries...")

    try:
        response = requests.get(repo_url).json()
        targets = ["aws", "azure", "gcp"]
        stats = {}
        mapping = {}

        for provider in targets:
            stats[provider] = 0
            mapping[provider] = {}

        for item in response.get("tree", []):
            path = item["path"]

            if path.startswith("resources/") and path.endswith(".png"):
                parts = path.split("/")
                if len(parts) >= 4:
                    provider = parts[1]
                    if provider in targets:
                        category = parts[2]
                        service_name = parts[-1].replace(".png", "")
                        download_url = raw_base + path

                        # Create directories
                        os.makedirs(f"icons/{provider}/{category}", exist_ok=True)
                        file_path = f"icons/{provider}/{category}/{service_name}.png"

                        # Download icon
                        if not os.path.exists(file_path):
                            img_data = requests.get(download_url).content
                            with open(file_path, "wb") as f:
                                f.write(img_data)
                            print(f"[{provider.upper()}] {category}/{service_name}")
                        else:
                            print(f"[{provider.upper()}] ⏭ {category}/{service_name}")

                        stats[provider] += 1
                        mapping[provider][service_name] = (
                            f"{category}/{service_name}.png"
                        )

        # Save the mapping
        with open("icons/service_icon_mapping.json", "w") as f:
            json.dump(mapping, f, indent=2)

        print("\nDownload Complete!")
        for provider, count in stats.items():
            print(f"   {provider.upper()}: {count} icons")

        print(f"\nMapping saved to: icons/service_icon_mapping.json")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    download_all_cloud_icons()
