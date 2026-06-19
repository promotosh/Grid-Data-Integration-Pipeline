import requests
from pathlib import Path

files = {
    'branch.csv': 'https://zenodo.org/record/7123537/files/branch.csv',
    'node.csv': 'https://zenodo.org/record/7123537/files/node.csv',
    'load_data.csv': 'https://zenodo.org/record/7123537/files/load_data.csv'
}

data_dir = Path('data/raw/zenodo')
for name, url in files.items():
    print(f"Downloading {name}...")
    r = requests.get(url)
    (data_dir / name).write_bytes(r.content)
    print(f"✓ {name}")
