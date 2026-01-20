import json
from pathlib import Path

def load_cloud_services(path="cloud_services.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
