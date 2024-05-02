import os
import shutil
import time
import json
import zipfile
import argparse
import subprocess
import math

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

# Update 'meta.json' file
meta_file_path = os.path.join(addon_path, 'meta.json')
with open(meta_file_path, 'r+') as f:
    meta = json.load(f)
    if args.l:
        meta['version'] = round(float(meta['version']) + 0.01, 2)  # Increment in the hundredths place
    else:
        meta['version'] = round(float(meta['version']) + 0.1, 1)  # Increment in the tenths place
    f.seek(0)
    json.dump(meta, f)
    f.truncate()

# Name of the output .ankiaddon file
output_file = f'{addon_dir}_v{meta["version"]}.ankiaddon'

# Create a 'manifest.json' file
manifest = {
    "package": addon_dir,
    "name": "Anking Tables",
    "conflicts": [],
    "mod": int(time.time())
}

with open(os.path.join(addon_path, 'manifest.json'), 'w') as f:
    json.dump(manifest, f)

# Create a zip file (overwrites existing file if it exists)
with zipfile.ZipFile(output_file, 'w') as zipf:
    for root, dirs, files in os.walk(addon_path):
        for file in files:
            if '__pycache__' not in root:
                zipf.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file), addon_path))

def round_down(f, decimals):
    factor = 10.0 ** decimals
    return math.floor(f * factor) / factor

if args.c or args.t:
    # Push a new release
    # Update 'meta.json' file
    meta_file_path = os.path.join(addon_path, 'meta.json')
    with open(meta_file_path, 'r+') as f:
        meta = json.load(f)
        if args.l:
            meta['version'] = round_down(float(meta['version']) + 0.01, 2)  # Increment in the hundredths place
        elif args.c or args.t:
            meta['version'] = round_down(float(meta['version']) + 0.1, 1)  # Increment in the tenths place
        f.seek(0)
        json.dump(meta, f)
        f.truncate()

    # Name of the output .ankiaddon file
    output_file = f'{addon_dir}_v{meta["version"]}.ankiaddon'

    # Create a 'manifest.json' file
    manifest = {
        "package": addon_dir,
        "name": "Anking Tables",
        "conflicts": [],
        "mod": int(time.time())
    }

    with open(os.path.join(addon_path, 'manifest.json'), 'w') as f:
        json.dump(manifest, f)

    # Create a zip file (overwrites existing file if it exists)
    with zipfile.ZipFile(output_file, 'w') as zipf:
        for root, dirs, files in os.walk(addon_path):
            for file in files:
                if '__pycache__' not in root:
                    zipf.write(os.path.join(root, file),
                               os.path.relpath(os.path.join(root, file), addon_path))

    # Push a new release
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', f'v{meta["version"]}'], check=True)
    subprocess.run(['git', 'tag', f'v{meta["version"]}'], check=True)
    subprocess.run(['git', 'push', '--tags'], check=True)