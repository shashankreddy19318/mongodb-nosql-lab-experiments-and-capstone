import urllib.request
import json
import base64
import os

files_to_download = [
    "chapter-08/docker-compose-replicaset.yml",
    "chapter-08/lab_01_deploy_replicaset.sh",
    "chapter-08/lab_02_failover_observer.py",
    "chapter-08/README.md",
    "chapter-09/lab_01_write_concern_latency.py",
    "chapter-09/lab_02_simulate_partition.sh",
    "chapter-09/README.md"
]

base_api = "https://api.github.com/repos/sujeetjagtap/NoSQL-Databases-using-MongoDB/contents/"

for file_path in files_to_download:
    url = base_api + file_path
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Fetching {file_path}...")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            content_bytes = base64.b64decode(data['content'])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(content_bytes)
            print(f"Saved {file_path} ({len(content_bytes)} bytes)")
    except Exception as e:
        print(f"Error fetching {file_path}: {e}")
