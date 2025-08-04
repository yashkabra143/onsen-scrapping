import gspread
from google.oauth2.service_account import Credentials
import os
import sys

# Default headers used when creating a new worksheet
HEADER_ROW = [
    "Date",
    "Time",
    "Slots_Booked",
    "Slots_Available",
    "Total_Capacity",
    "Occupancy_Rate",
    "Revenue_Estimated",
    "Horizon_Days",
    "Scraped_At",
    "Data_Source",
    "Created_At",
]

# Extended headers used for day-based tabs if none are present
EXTENDED_HEADER_ROW = [
    "Date",
    "Time",
    "Slots_Booked",
    "Slots_Available",
    "Total_Capacity",
    "Occupancy_Rate",
    "Revenue_Estimated",
    "Horizon_Days",
    "Scraped_At",
    "Data_Source",
    "Date",
    "Time",
    "Client_Slots_Booked",
    "Client_Slots_Available",
    "Client_Total_Capacity",
    "Client_Occupancy_Rate",
    "Client_Revenue_Projected",
    "Competitor_Slots_Booked",
    "Competitor_Occupancy_Rate",
    "Competitor_Revenue",
    "Performance_Factor",
    "Reduction_Factor",
    "Revenue_Per_Spa",
    "Horizon_Days",
    "Data_Source",
    "Created_At",
]


def apply_default_formatting(worksheet, headers):
    """Apply default formatting to keep headers styled consistently."""
    header_format = {"textFormat": {"bold": True}}
    end_col = chr(ord("A") + len(headers) - 1)
    worksheet.format(f"A1:{end_col}1", header_format)

def authenticate():
    """Authenticate with Google Sheets"""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Try to find the JSON keyfile
    json_files = [
        "onsen-scraping-e41c80c00b93.json",
        "onsen-scraping-e41c80c00b930a5025ad1c8704c784a2c7e35b66.json",
        os.path.join(os.path.dirname(__file__), "onsen-scraping-e41c80c00b93.json")
    ]
    
    json_keyfile = None
    for file in json_files:
        if os.path.exists(file):
            json_keyfile = file
            break
    
    if not json_keyfile:
        raise FileNotFoundError(f"Could not find credentials file. Tried: {json_files}")
    
    creds = Credentials.from_service_account_file(json_keyfile, scopes=scope)
    client = gspread.authorize(creds)
    return client, json_keyfile

def check_if_sheet_exists(sheet_id, tab_name):
    """Check if a worksheet exists in the spreadsheet"""
    try:
        client, _ = authenticate()
        sheet = client.open_by_key(sheet_id)
        existing_worksheets = [ws.title for ws in sheet.worksheets()]
        return tab_name in existing_worksheets
    except Exception as e:
        print(f"Error checking sheet existence: {e}")
        return False

def write_to_sheets(sheet_id, tab_name, data):
    """
    Write data to a specific tab in Google Sheets, replacing previous data rows
    while preserving headers and formatting.

    Args:
        sheet_id: Google Sheets ID
        tab_name: Name of the tab/worksheet to write to
        data: 2D list of data to write
    """
    try:
        client, json_keyfile = authenticate()
        print(f"Using credentials file: {json_keyfile}", flush=True)

        # Open the spreadsheet
        sheet = client.open_by_key(sheet_id)

        # Try to select the worksheet, create if it doesn't exist
        try:
            worksheet = sheet.worksheet(tab_name)
            print(f"Found existing worksheet: {tab_name}", flush=True)
        except gspread.exceptions.WorksheetNotFound:
            print(f"Creating new worksheet: {tab_name}", flush=True)
            cols = len(data[0]) if data else len(HEADER_ROW)
            worksheet = sheet.add_worksheet(title=tab_name, rows=1000, cols=cols)

        # Determine headers for formatting and clearing
        headers_from_data = data[0] if data else HEADER_ROW
        end_col = chr(ord('A') + len(headers_from_data) - 1)

        # Clear existing content but keep headers and formatting
        worksheet.batch_clear([f"A2:{end_col}"])

        # Write the data
        if data:
            worksheet.update(values=data, range_name='A1')
            apply_default_formatting(worksheet, headers_from_data)
            print(f"✅ Successfully wrote {len(data)} rows to {tab_name}", flush=True)
        else:
            print(f"⚠️ No data to write to {tab_name}", flush=True)

    except Exception as e:
        print(f"❌ Error writing to sheets: {str(e)}", flush=True)
        raise

def append_to_sheets(sheet_id, tab_name, data, headers=None):
    """
    Append data to a specific tab in Google Sheets (keeps existing data).

    Args:
        sheet_id: Google Sheets ID
        tab_name: Name of the tab/worksheet to append to
        data: 2D list of data to append (without headers)
        headers: Optional list of column headers to write if sheet is created
    """
    try:
        client, json_keyfile = authenticate()
        print(f"Using credentials file: {json_keyfile}", flush=True)

        normalized_tab = tab_name.replace(" ", "").lower()
        special_tabs = {"sameday", "sevendays", "thirtydays", "nintydays"}
        if headers is None:
            headers = EXTENDED_HEADER_ROW if normalized_tab in special_tabs else HEADER_ROW

        sheet = client.open_by_key(sheet_id)

        try:
            worksheet = sheet.worksheet(tab_name)
            print(f"Found existing worksheet: {tab_name}", flush=True)
            all_values = worksheet.get_all_values()
            if not all_values or all_values[0] != headers:
                worksheet.update("A1", [headers])
                apply_default_formatting(worksheet, headers)
                next_row = 2
            else:
                next_row = len(all_values) + 1
        except gspread.exceptions.WorksheetNotFound:
            print(f"Creating new worksheet: {tab_name}", flush=True)
            worksheet = sheet.add_worksheet(title=tab_name, rows=1000, cols=len(headers))
            worksheet.update("A1", [headers])
            apply_default_formatting(worksheet, headers)
            next_row = 2

        if data:
            num_rows = len(data)
            num_cols = len(data[0]) if data else 0
            end_row = next_row + num_rows - 1
            end_col = chr(ord('A') + num_cols - 1)
            range_name = f'A{next_row}:{end_col}{end_row}'
            worksheet.update(values=data, range_name=range_name)
            apply_default_formatting(worksheet, headers)
            print(f"✅ Successfully appended {len(data)} rows to {tab_name} starting at row {next_row}", flush=True)
        else:
            print(f"⚠️ No data to append to {tab_name}", flush=True)

    except Exception as e:
        print(f"❌ Error appending to sheets: {str(e)}", flush=True)
        raise
