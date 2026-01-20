import json
from pathlib import Path


def load_cloud_icons(path="cloud_catalog.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def load_public_cloud_icons(path="public_cloud_catalog.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
