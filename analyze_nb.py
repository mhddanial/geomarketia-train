import json
import re

with open('geomarketia_train.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    source = cell.get('source', [])
    first_line = source[0].strip() if source else ''
    cell_type = cell['cell_type']
    
    if cell_type == 'markdown':
        # Get the first header
        header = ''
        for line in source:
            line = line.strip()
            if line.startswith('#'):
                header = line
                break
        if not header and first_line:
            header = first_line[:50]
        print(f"[{i:02d}] MD: {header}")
    else:
        # Code cell, get first comment
        header = ''
        for line in source:
            line = line.strip()
            if line.startswith('#'):
                header = line
                break
        print(f"[{i:02d}] CD: {header}")
