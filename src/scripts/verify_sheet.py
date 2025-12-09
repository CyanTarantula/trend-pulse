import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Load env from web directory
env_path = os.path.join(os.path.dirname(__file__), "../web/.env.local")
load_dotenv(env_path)

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
SHEET_ID = os.environ.get("SHEET_ID")
if SHEET_ID and (SHEET_ID.startswith('"') or SHEET_ID.startswith("'")):
    SHEET_ID = SHEET_ID[1:-1]
CREDS_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

creds_dict = json.loads(CREDS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

for tab in ["General", "Gen Z"]:
    try:
        ws = sheet.worksheet(tab)
        records = ws.get_all_records()
        print(f"\n--- {tab} Trends ---")
        for r in records[-5:]:  # Show last 5
            print(f"- {r.get('Trend')}")
    except:
        pass
