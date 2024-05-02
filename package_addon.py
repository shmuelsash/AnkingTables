import os
import shutil
import time
import json
import zipfile
import argparse
import subprocess
import math
import re

def update_script_version(version):
    with open('package_addon.py', 'r') as file:
        content = file.read()

    new_content = re.sub(r'v\d+\.\d+', f'v{version}', content)

    with open('package_addon.py', 'w') as file:
        file.write(new_content)

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-c', action='store_true')
parser.add_argument('-t', action='store_true')
parser.add_argument('-l', action='store_true')
args = parser.parse_args()

# Name of your add-on directory
addon_dir = 'anking_tables'

# Path to the add-on directory
addon_path = os.path.join(os.getcwd(), addon_dir)

def round_down(f, decimals):
    factor = 10.0 ** decimals
    return math.floor(f * factor) / factor

def update_meta_file(increment):
    # Update 'meta.json' file
    meta_file_path = os.path.join(addon_path, 'meta.json')
    with open(meta_file_path, 'r+') as f:
        meta = json.load(f)
        meta['version'] = round_down(float(meta['version']) + increment, 2 if increment == 0.01 else 1)
        f.seek(0)
        json.dump(meta, f)
        f.truncate()
    return meta

def create_manifest_file():
    # Create a 'manifest.json' file
    manifest = {
        "package": addon_dir,
        "name": "Anking Tables",
        "conflicts": [],
        "mod": int(time.time())
    }

    with open(os.path.join(addon_path, 'manifest.json'), 'w') as f:
        json.dump(manifest, f)

def create_zip_file(meta):
    # Name of the output .ankiaddon file
    output_file = f'{addon_dir}_v{meta["version"]}.ankiaddon'

    # Create a zip file (overwrites existing file if it exists)
    with zipfile.ZipFile(output_file, 'w') as zipf:
        for root, dirs, files in os.walk(addon_path):
            for file in files:
                if '__pycache__' not in root:
                    zipf.write(os.path.join(root, file),
                               os.path.relpath(os.path.join(root, file), addon_path))

def git_operations(meta, test=False):
    # Push a new release
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', check=True)
    if test:
        subprocess.run(['git', 'checkout', '-b', check=True)
    subprocess.run(['git', 'tag', f'v{meta["version"]}'], check=True)
    subprocess.run(['git', 'push', '--tags'], check=True)

if args.c:
    meta = update_meta_file(0.1)
    update_script_version(meta['version'])
    create_manifest_file()
    create_zip_file(meta)
    git_operations(meta)

if args.t:
    meta = update_meta_file(0.1)
    update_script_version(meta['version'])
    create_manifest_file()
    create_zip_file(meta)
    git_operations(meta, test=True)
    create_github_release(meta)
    create_github_fork('shmuelsash/AnkingTables')

if args.l:
    meta = update_meta_file(0.01)
    create_manifest_file()
    create_zip_file(meta)
