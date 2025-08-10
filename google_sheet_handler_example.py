import gspread
from google.oauth2.service_account import Credentials

# Path to your service account key
SERVICE_ACCOUNT_FILE = 'custom-search-1731290468460-07b857abd390.json'

# Define the scopes needed - Only Sheets API for URL method
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets'  # Only this is needed when using URL
]

# Authenticate using the service account
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

# METHOD 1: Open by URL (RECOMMENDED - Most reliable)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wPqGyc7sgGLUO4xHe60hdqydXw5jxY704ocVmPH6IZc/edit?gid=0#gid=0"

try:
    sheet = gc.open_by_url(SHEET_URL)
    worksheet = sheet.sheet1  # or sheet.get_worksheet(0) for first sheet
    print("[SUCCESS] Successfully opened spreadsheet by URL!")

except gspread.exceptions.SpreadsheetNotFound:
    print("[ERROR] Spreadsheet not found or not accessible to service account")
    print("Make sure to:")
    print("1. Share the spreadsheet with: google-sheet-api-access@custom-search-1731290468460.iam.gserviceaccount.com")
    print("2. Give it Editor permissions")
    print("3. Check that the URL is correct")
    exit()

except Exception as e:
    print(f"[ERROR] Error: {e}")
    exit()

# OTHER METHODS (alternatives):
# Method 2: Open by spreadsheet ID only
# sheet_id = "1wPqGyc7sgGLUO4xHe60hdqydXw5jxY704ocVmPH6IZc"
# sheet = gc.open_by_key(sheet_id)

# Method 3: Open by name (requires Drive API scope - NOT NEEDED for URL method)
# sheet = gc.open("X list")

# Read all data
data = worksheet.get_all_values()
print("\nCurrent Sheet Data:")
for i, row in enumerate(data, 1):
    print(f"Row {i}: {row}")

# Write to a cell - Fixed syntax
worksheet.update_acell('A1', 'Hello from Python!')
print("\n[SUCCESS] Updated cell A1!")

# Alternative methods you can use:
print("\nOther useful methods:")
print("# worksheet.update('A1:B2', [['Name', 'Age'], ['John', 25]])")  # Update range
print("# worksheet.append_row(['New', 'Row', 'Data'])")  # Add new row
print("# cell_value = worksheet.acell('A1').value")  # Read single cell
print("# worksheet.update_acell('B1', 'Single cell update')")  # Update single cell