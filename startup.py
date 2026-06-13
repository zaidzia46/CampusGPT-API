"""
startup.py
-----------
Writes credentials.json and sheets_config.json from environment
variables to disk before the app starts. Required because these
files are gitignored and not present in deployment.

Run this before starting uvicorn.
"""

import os
import json
from pathlib import Path

UNIDATA_DIR = Path(__file__).parent / "UNIdata"
UNIDATA_DIR.mkdir(exist_ok=True)


def write_file_from_env(env_var: str, filename: str):
    content = os.getenv(env_var)
    if not content:
        print(f"  [startup] WARNING: {env_var} not set — skipping {filename}")
        return

    filepath = UNIDATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [startup] Wrote {filepath}")


if __name__ == "__main__":
    write_file_from_env("GOOGLE_CREDENTIALS_JSON", "credentials.json")
    write_file_from_env("SHEETS_CONFIG_JSON",      "sheets_config.json")
    print("  [startup] Done.")