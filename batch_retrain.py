import json
import glob
import os
import subprocess
import sys

def modify_notebook(notebook_path, target_db):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = cell['source']
            for i, line in enumerate(source):
                if line.startswith('TARGET_DB_FILE = '):
                    source[i] = f'TARGET_DB_FILE = "{target_db}"  # auto-patched\n'
                    print(f"Patched TARGET_DB_FILE to {target_db}")
                    break

    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)

def run_notebook(notebook_path):
    print(f"\n--- Running notebook {notebook_path} ---")
    # run with jupyter nbconvert
    cmd = [
        sys.executable, "-m", "jupyter", "nbconvert",
        "--execute",
        "--to", "notebook",
        "--inplace",
        "--ExecutePreprocessor.timeout=-1",
        notebook_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAILED to run notebook for {notebook_path}")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    print("SUCCESS")
    return True

if __name__ == "__main__":
    dbs = glob.glob('content/data/raw/*.db')
    dbs = [os.path.basename(db) for db in dbs]
    
    # We will process all databases
    success_count = 0
    notebook_path = "geomarketia_train.ipynb"
    
    for db in dbs:
        print(f"\n==========================================")
        print(f"Processing Database: {db}")
        print(f"==========================================")
        modify_notebook(notebook_path, db)
        if run_notebook(notebook_path):
            success_count += 1
            
    print(f"\nDone! Successfully trained {success_count} out of {len(dbs)} databases.")
