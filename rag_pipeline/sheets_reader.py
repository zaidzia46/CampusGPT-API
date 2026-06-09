import json
from pathlib import Path
import time
import gspread
import pandas as pd
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials

ROOT        = Path(__file__).parent.parent
CONFIG_FILE = str(ROOT / "UNIdata" / "sheets_config.json")

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

def get_client():
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    
    creds_path = str(ROOT / "UNIdata" / config["credentials_file"])
    creds  = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds), config

def _run_with_retry(operation, retries: int = 3, delay: int = 2):
    for attempt in range(retries):
        try:
            return operation()
        except APIError as e:
            if "503" not in str(e) or attempt == retries - 1:
                raise
            time.sleep(delay * (attempt + 1))

def read_sheet(topic: str, sheet_name: str = None, header_row: int = 2) -> pd.DataFrame:
    """
    Reads a Google Sheet and returns a cleaned DataFrame.

    topic      → key in sheets_config.json (e.g. 'scholarships')
    sheet_name → exact tab name in the Google Sheet
    header_row → which row has the column headers (0-indexed)
    """
    client, config = get_client()

    sheet_config = config["sheets"][topic]
    sheet_id     = sheet_config["sheet_id"]
    tab_name     = sheet_name or sheet_config["sheet_name"]
    sheet        = _run_with_retry(lambda: client.open_by_key(sheet_id))
    ws           = _run_with_retry(lambda: sheet.worksheet(tab_name))

    # Get all values as a list of lists
    all_rows = _run_with_retry(ws.get_all_values)

    # Use the specified row as headers
    headers = all_rows[header_row]
    data    = all_rows[header_row + 1:]

    df = pd.DataFrame(data, columns=headers)

    # Replace empty strings with None
    df = df.replace("", None)

    return df

def append_to_faculty_sheet(row: dict):
    """Writes approved faculty submission to Google Sheet."""
    gc, config = get_client()
    sheet_config = config["sheets"]["faculty_knowledge_base"]
    sheet = _run_with_retry(lambda: gc.open_by_key(sheet_config["sheet_id"]))
    ws = _run_with_retry(lambda: sheet.worksheet(sheet_config["sheet_name"]))

    # column order must match sheet headers exactly
    values = [
        row["faculty_name"],
        row["topic"],
        row["detail"],
        row["tags"],
        row["file_url"],
    ]
    _run_with_retry(lambda: ws.append_row(values))
