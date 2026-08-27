#!/usr/bin/env python3
"""Docker Hub API helper."""
import json
import urllib.request

def get_image_tags(image, limit=10):
    """Get tags for a Docker Hub image."""
    url = f"https://hub.docker.com/v2/repositories/{image}/tags?page_size={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "homelab-scripts"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    
    tags = []
    for result in data.get("results", []):
        tags.append({
            "name": result["name"],
            "last_updated": result["last_updated"],
            "full_size": result.get("full_size", 0)
        })
    return tags

if __name__ == "__main__":
    import sys
    image = sys.argv[1] if len(sys.argv) > 1 else "library/nginx"
    tags = get_image_tags(image)
    for tag in tags[:5]:
        print(f"  {tag['name']}: {tag['last_updated']}")
