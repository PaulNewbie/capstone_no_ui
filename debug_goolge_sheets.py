# debug_google_sheets.py - Debug Google Sheets connection

import os
import json

def debug_google_sheets():
    """Debug Google Sheets connection and data structure"""
    
    print("🔍 MotorPass Google Sheets Debug Tool")
    print("=" * 50)
    
    # Check credentials file
    creds_path = "json_folder/credentials.json"
    if not os.path.exists(creds_path):
        print("❌ credentials.json not found!")
        print(f"📂 Expected location: {os.path.abspath(creds_path)}")
        print("💡 Make sure you've downloaded your service account JSON file")
        return
    
    print("✅ credentials.json found")
    
    # Check credentials content
    try:
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds_data]
        
        if missing_fields:
            print(f"❌ Missing fields in credentials: {missing_fields}")
            return
        
        print(f"✅ Credentials valid for: {creds_data.get('client_email', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return
    
    # Test Google Sheets connection
    try:
        print("\n🔗 Testing Google Sheets connection...")
        
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)
        
        print("✅ Google Sheets client authorized")
        
        # Try to open the spreadsheet
        sheet_name = "MotorPass Registration Form (Responses)"
        print(f"📊 Attempting to open: '{sheet_name}'")
        
        sheet = client.open(sheet_name).sheet1
        print("✅ Spreadsheet opened successfully")
        
        # Get headers
        headers = sheet.row_values(1)
        print(f"\n📋 Found {len(headers)} columns:")
        for i, header in enumerate(headers, 1):
            print(f"   {i:2d}. {header}")
        
        # Get row count
        all_records = sheet.get_all_records()
        print(f"\n📊 Total data rows: {len(all_records)}")
        
        if len(all_records) > 0:
            print("\n📝 Sample data (first row):")
            first_row = all_records[0]
            for key, value in first_row.items():
                print(f"   {key}: {value}")
        
        # Check for expected columns
        expected_columns = [
            'Full Name', 'License Number', 'License Expiration Date',
            'Plate Number of the Motorcycle', 'Course', 'Student No.',
            'Staff Role', 'Staff No.'
        ]
        
        print(f"\n🔍 Column Check:")
        for expected in expected_columns:
            found = any(expected.lower() in header.lower() for header in headers)
            status = "✅" if found else "❌"
            print(f"   {status} {expected}")
        
        print(f"\n🎉 Google Sheets connection successful!")
        print(f"💡 You can now try the sync function again")
        
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"❌ Spreadsheet '{sheet_name}' not found")
        print("💡 Check the exact name of your Google Sheet")
        print("💡 Make sure the service account has access to the sheet")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check your internet connection")
        print("💡 Ensure the service account has proper permissions")

if __name__ == "__main__":
    debug_google_sheets()
