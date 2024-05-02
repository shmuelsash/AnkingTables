import os
import shutil
import time
import json
import zipfile

# Name of your add-on directory
addon_dir = 'anking_tables'

# Path to the add-on directory
addon_path = os.path.join(os.getcwd(), addon_dir)

# Update 'meta.json' file
meta_file_path = os.path.join(addon_path, 'meta.json')
with open(meta_file_path, 'r+') as f:
    meta = json.load(f)
    meta['version'] = round(float(meta['version']) + 0.1, 1)  # Convert to float
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