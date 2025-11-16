from dotenv import load_dotenv
import os
import json
from typing import List, Dict, Optional

import gspread
import requests
import csv
from io import StringIO
import re

load_dotenv()

INSTRUCTIONS_QUESTIONS_SPREADSHEET = os.getenv("INSTRUCTIONS_QUESTIONS_SPREADSHEET")
INSTRUCTIONS_WELCOME_SPREADSHEET = os.getenv("INSTRUCTIONS_WELCOME_SPREADSHEET")
INSTRUCTIONS_OBJECTIONS_SPREADSHEET = os.getenv("INSTRUCTIONS_OBJECTIONS_SPREADSHEET")
INSTRUCTIONS_REACTIONS_SPREADSHEET = os.getenv("INSTRUCTIONS_REACTIONS_SPREADSHEET")
INSTRUCTIONS_DISTRICTS_SPREADSHEET = os.getenv("INSTRUCTIONS_DISTRICTS_SPREADSHEET")

INSTRUCTIONS_QUESTIONS_GID = os.getenv("INSTRUCTIONS_QUESTIONS_GID", "0")
INSTRUCTIONS_WELCOME_GID = os.getenv("INSTRUCTIONS_WELCOME_GID", "0")
INSTRUCTIONS_OBJECTIONS_GID = os.getenv("INSTRUCTIONS_OBJECTIONS_GID", "0")
INSTRUCTIONS_REACTIONS_GID = os.getenv("INSTRUCTIONS_REACTIONS_GID", "0")
INSTRUCTIONS_DISTRICTS_GID = os.getenv("INSTRUCTIONS_DISTRICTS_GID", "0")


def _parse_sheet_ref(ref: Optional[str]) -> Dict[str, Optional[str]]:
    if not ref:
        return {"id": None, "gid": None}
    ref = ref.strip().strip('"').strip("'")
    if ref.startswith("http://") or ref.startswith("https://"):
        m = re.search(r"/d/([a-zA-Z0-9-_]+)", ref)
        sheet_id = m.group(1) if m else None
        mg = re.search(r"[?&#]gid=(\d+)", ref)
        gid = mg.group(1) if mg else None
        return {"id": sheet_id, "gid": gid}
    return {"id": ref, "gid": None}


def _resolve_sheet_params(env_ref: Optional[str], env_gid: Optional[str]) -> Dict[str, Optional[str]]:
    parsed = _parse_sheet_ref(env_ref)
    gid = (env_gid or '').strip()
    if not gid:
        gid = parsed.get('gid') or '0'
    return {"id": parsed.get('id'), "gid": gid}

def _get_gspread_client() -> gspread.Client:

    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    inline_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if creds_path and os.path.isfile(creds_path):
        return gspread.service_account(filename=creds_path)

    if inline_json:
        data = json.loads(inline_json)
        return gspread.service_account_from_dict(data)

    raise RuntimeError(
        "Google credentials not configured. Set GOOGLE_APPLICATION_CREDENTIALS to a JSON file path "
        "or GOOGLE_SERVICE_ACCOUNT_JSON to inline JSON."
    )


def _fetch_sheet_as_dicts(
    spreadsheet_id: str,
    worksheet_index: int = 0,
    range_name: Optional[str] = None,
) -> List[Dict[str, str]]:
    if not spreadsheet_id:
        return []

    client = _get_gspread_client()
    sh = client.open_by_key(spreadsheet_id)
    ws = sh.get_worksheet(worksheet_index)
    if ws is None:
        return []

    if range_name:
        values = ws.get(range_name)
    else:
        values = ws.get_all_values()

    if not values:
        return []

    headers = [h.strip() for h in values[0]]
    rows = []
    for row in values[1:]:
        if len(row) < len(headers):
            row = row + [""] * (len(headers) - len(row))
        rows.append({headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))})
    return rows


def _fetch_public_csv_as_dicts(spreadsheet_id: str, gid: str = "0") -> List[Dict[str, str]]:
    if not spreadsheet_id:
        return []
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    csv_bytes = resp.content
    csv_text = csv_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.reader(StringIO(csv_text))
    rows = list(reader)
    if not rows:
        return []
    headers = [h.strip() for h in rows[0]]
    out: List[Dict[str, str]] = []
    for row in rows[1:]:
        if len(row) < len(headers):
            row = row + [""] * (len(headers) - len(row))
        out.append({headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))})
    return out


def _fetch_sheet_auto(spreadsheet_id: str, gid: str = "0") -> List[Dict[str, str]]:
    try:
        return _fetch_sheet_as_dicts(spreadsheet_id)
    except RuntimeError:
        return _fetch_public_csv_as_dicts(spreadsheet_id, gid)


def get_instructions_questions() -> List[Dict[str, str]]:
    params = _resolve_sheet_params(INSTRUCTIONS_QUESTIONS_SPREADSHEET, INSTRUCTIONS_QUESTIONS_GID)
    return _fetch_sheet_auto(params["id"], params["gid"])

def get_instructions_welcome() -> List[Dict[str, str]]:
    params = _resolve_sheet_params(INSTRUCTIONS_WELCOME_SPREADSHEET, INSTRUCTIONS_WELCOME_GID)
    return _fetch_sheet_auto(params["id"], params["gid"])

def get_instructions_objections() -> List[Dict[str, str]]:
    params = _resolve_sheet_params(INSTRUCTIONS_OBJECTIONS_SPREADSHEET, INSTRUCTIONS_OBJECTIONS_GID)
    return _fetch_sheet_auto(params["id"], params["gid"])

def get_instructions_reactions() -> List[Dict[str, str]]:
    params = _resolve_sheet_params(INSTRUCTIONS_REACTIONS_SPREADSHEET, INSTRUCTIONS_REACTIONS_GID)
    return _fetch_sheet_auto(params["id"], params["gid"])

def get_instructions_districts() -> List[Dict[str, str]]:
    params = _resolve_sheet_params(INSTRUCTIONS_DISTRICTS_SPREADSHEET, INSTRUCTIONS_DISTRICTS_GID)
    return _fetch_sheet_auto(params["id"], params["gid"])


# if __name__ == "__main__":
#     print(len(get_instructions_questions()))