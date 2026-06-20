import requests
import json
from pathlib import Path

RECORD_ID = "7123537"
BASE_URL = f"https://zenodo.org/api/records/{RECORD_ID}"
data_dir = Path('data/raw/zenodo')
data_dir.mkdir(parents=True, exist_ok=True)

print("Fetching file list from Zenodo...")
files = requests.get(BASE_URL).json()['files']

for f in files:
    name = f['key']
    url = f['links']['self']
    print(f"Downloading {name}...")
    r = requests.get(url, allow_redirects=True)
    r.raise_for_status()
    (data_dir / name).write_bytes(r.content)
    print(f"✓ {name}")

print(f"\n✅ Downloaded {len(files)} files to {data_dir}")
