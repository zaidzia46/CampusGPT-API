# create_zip.py — run this in your project root
import zipfile
import os
from pathlib import Path

vectordb_path = Path("UNIdata/vectordb")
zip_path      = Path("vectordb_linux.zip")

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for file_path in vectordb_path.rglob('*'):
        if file_path.is_file():
            # use forward slashes explicitly
            arcname = file_path.relative_to(vectordb_path).as_posix()
            zf.write(file_path, arcname)
            print(f"Added: {arcname}")

print(f"\nDone → {zip_path}")