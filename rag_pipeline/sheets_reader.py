import json
from pathlib import Path
import gspread
import pandas as pd
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

def read_sheet(topic: str, sheet_name: str, header_row: int = 2) -> pd.DataFrame:
    """
    Reads a Google Sheet and returns a cleaned DataFrame.

    topic      → key in sheets_config.json (e.g. 'scholarships')
    sheet_name → exact tab name in the Google Sheet
    header_row → which row has the column headers (0-indexed)
    """
    client, config = get_client()

    sheet_id = config["sheets"][topic]["sheet_id"]
    sheet    = client.open_by_key(sheet_id)
    ws       = sheet.worksheet(sheet_name)

    # Get all values as a list of lists
    all_rows = ws.get_all_values()

    # Use the specified row as headers
    headers = all_rows[header_row]
    data    = all_rows[header_row + 1:]

    df = pd.DataFrame(data, columns=headers)

    # Replace empty strings with None
    df = df.replace("", None)

    return df