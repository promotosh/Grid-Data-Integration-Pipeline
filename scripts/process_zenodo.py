import pandas as pd
from pathlib import Path

data_dir = Path('data/raw/zenodo')

try:
    branches = pd.read_csv(data_dir / 'branch.csv', on_bad_lines='skip')
    nodes = pd.read_csv(data_dir / 'node.csv', on_bad_lines='skip')
    loads = pd.read_csv(data_dir / 'load_data.csv', on_bad_lines='skip')
    
    print(f"✓ Branches: {len(branches)}")
    print(f"✓ Nodes: {len(nodes)}")
    print(f"✓ Loads: {len(loads)}")
    print("✅ SUCCESS!")
except Exception as e:
    print(f"Error: {e}")
