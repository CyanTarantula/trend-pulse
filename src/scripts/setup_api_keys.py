import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env
env_path = os.path.join(os.path.dirname(__file__), "../../src/web/.env.local")
load_dotenv(env_path)

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

SHEET_ID = os.environ.get("SHEET_ID")
if SHEET_ID and (SHEET_ID.startswith('"') or SHEET_ID.startswith("'")):
    SHEET_ID = SHEET_ID[1:-1]

CREDS_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")


def setup_api_keys_sheet():
    if not CREDS_JSON or not SHEET_ID:
        logger.error("Missing credentials or Sheet ID in environment.")
        return

    try:
        creds_dict = json.loads(CREDS_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID)

        tab_name = "ApiKeys"
        try:
            worksheet = sheet.worksheet(tab_name)
            logger.info(f"Worksheet '{tab_name}' already exists.")
        except gspread.WorksheetNotFound:
            logger.info(f"Worksheet '{tab_name}' not found. Creating...")
            worksheet = sheet.add_worksheet(title=tab_name, rows=100, cols=4)
            worksheet.append_row(["ApiKey", "AppName", "OwnerEmail", "Active"])
            logger.info(f"Worksheet '{tab_name}' created successfully with headers.")

    except Exception as e:
        logger.error(f"Error checking/creating sheet: {e}")


if __name__ == "__main__":
    setup_api_keys_sheet()
