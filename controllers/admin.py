# controllers/admin.py 

from config import ADMIN_MENU
from services.fingerprint import *

from database.db_operations import (
    get_all_time_records,
    clear_all_time_records,
    get_students_currently_in,
    get_database_stats
)

from utils.display_helpers import (
	display_menu, 
	get_user_input, 
	confirm_action, 
	display_separator
)

import time
import json
import os

# =================== ADMIN DATABASE FUNCTIONS ===================

def load_admin_database():
    """Load admin database (create if not exists)"""
    admin_file = "json_folder/admin_database.json"
    if os.path.exists(admin_file):
        try:
            with open(admin_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_admin_database(database):
    """Save admin database"""
    os.makedirs("json_folder", exist_ok=True)
    with open("json_folder/admin_database.json", 'w') as f:
        json.dump(database, f, indent=4)
        
# =================== SLOT MANAGEMENT FUNCTIONS ===================

def find_next_available_slot():
    """Automatically find the next available slot (skips slot 1 for admin)"""
    try:
        # Read current templates from sensor
        if finger.read_templates() != adafruit_fingerprint.OK:
            print("❌ Failed to read sensor templates")
            return None
        
        # Load fingerprint database
        database = load_fingerprint_database()
        
        # Find next available slot starting from 2 (skip admin slot 1)
        for slot in range(2, finger.library_size + 1):
            if str(slot) not in database:
                print(f"🎯 Auto-assigned slot: #{slot}")
                return slot
        
        print("❌ No available slots found")
        return None
        
    except Exception as e:
        print(f"❌ Error finding available slot: {e}")
        return None

# =================== ADMIN AUTHENTICATION ===================

def check_admin_fingerprint_exists():
    """Check if admin fingerprint is enrolled in slot 1"""
    try:
        if finger.read_templates() != adafruit_fingerprint.OK:
            return False
        admin_db = load_admin_database()
        return "1" in admin_db
    except:
        return False

def enroll_admin_fingerprint():
    """Enroll admin fingerprint in slot 1"""
    print(f"\n🔐 ADMIN FINGERPRINT ENROLLMENT")
    print("⚠️  This will enroll the admin fingerprint at slot #1")
    
    # Check if admin exists
    try:
        admin_db = load_admin_database()
        if "1" in admin_db:
            print(f"⚠️  Admin fingerprint already exists!")
            if input("Replace it? (y/N): ").lower() != 'y':
                print("❌ Cancelled.")
                return False
    except:
        pass
    
    # Get admin name
    admin_name = input("Enter admin name: ").strip()
    if not admin_name:
        print("❌ Admin name required.")
        return False
    
    print(f"👤 Enrolling: {admin_name}")
    
    # Fingerprint enrollment process
    for fingerimg in range(1, 3):
        print(f"👆 Place finger {'(first time)' if fingerimg == 1 else '(again)'}...", end="")
        
        while finger.get_image() != adafruit_fingerprint.OK:
            print(".", end="")
        print("✅")

        print("🔄 Processing...", end="")
        if finger.image_2_tz(fingerimg) != adafruit_fingerprint.OK:
            print("❌ Failed")
            return False
        print("✅")

        if fingerimg == 1:
            print("✋ Remove finger")
            time.sleep(1)
            while finger.get_image() != adafruit_fingerprint.NOFINGER:
                pass

    print("🗝️ Creating model...", end="")
    if finger.create_model() != adafruit_fingerprint.OK:
        print("❌ Failed")
        return False
    print("✅")

    print(f"💾 Storing...", end="")
    if finger.store_model(1) == adafruit_fingerprint.OK:
        print("✅")
        
        # Save admin info
        admin_db = load_admin_database()
        admin_db["1"] = {
            "name": admin_name,
            "role": "admin",
            "enrolled_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_admin_database(admin_db)
        
        print(f"🎉 Admin enrolled: {admin_name}")
        return True
    else:
        print("❌ Storage failed")
        return False

def authenticate_admin():
    """Authenticate admin using fingerprint"""
    print("\n🔐 ADMIN AUTHENTICATION")
    print("👆 Place admin finger on sensor...")
    
    # Wait for finger and process
    while finger.get_image() != adafruit_fingerprint.OK:
        print(".", end="")
        time.sleep(0.1)
    
    print("\n🔄 Processing...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        print("❌ Failed to process")
        return False
    
    print("🔍 Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        print("❌ No match found")
        return False
    
    # Check if matched fingerprint is admin (slot 1)
    if finger.finger_id == 1:
        try:
            admin_db = load_admin_database()
            admin_name = admin_db.get("1", {}).get("name", "Admin User")
        except:
            admin_name = "Admin User"
        
        print(f"✅ Welcome Admin: {admin_name}")
        print(f"🎯 Confidence: {finger.confidence}")
        return True
    else:
        print("❌ Not an admin fingerprint")
        return False

# =================== ADMIN FUNCTIONS ===================
def admin_enroll():
    """Enroll new user (student or staff)"""
    if finger.read_templates() != adafruit_fingerprint.OK:
        print("❌ Failed to read templates")
        return
    
    print(f"📊 Current enrollments: {finger.template_count}")

    # Get slot (skip admin slot 1)
    location = find_next_available_slot()
    if location == 1:
        print("❌ Slot #1 reserved for admin. Use slot 2+")
        return
    
    success = enroll_finger_with_user_info(location)  
    print(f"{'✅ Success!' if success else '❌ Failed.'}")

def admin_view_enrolled():
    """Display all enrolled users (students and staff)"""
    database = load_fingerprint_database()
    if not database:
        print("📁 No users enrolled.")
        return
    
    print("\n👥 ENROLLED USERS:")
    display_separator()
    
    student_count = 0
    staff_count = 0
    
    for finger_id, info in database.items():
        # Skip admin slot
        if finger_id == "1":
            continue
        
        user_type = info.get('user_type', 'STUDENT')
        
        if user_type == 'STUDENT':
            student_count += 1
        else:
            staff_count += 1
        
        print(f"🆔 Slot: {finger_id}")
        print(f"👤 Name: {info['name']}")
        print(f"👥 Type: {user_type}")
        
        if user_type == 'STUDENT':
            print(f"🎓 Student ID: {info.get('student_id', 'N/A')}")
            print(f"📚 Course: {info.get('course', 'N/A')}")
        else:  # STAFF
            print(f"👔 Staff No.: {info.get('staff_no', 'N/A')}")
            print(f"💼 Role: {info.get('staff_role', 'N/A')}")
        
        print(f"🪪 License: {info.get('license_number', 'N/A')}")
        print(f"📅 License Exp: {info.get('license_expiration', 'N/A')}")
        print(f"🏍️ Plate: {info.get('plate_number', 'N/A')}")
        print(f"🕒 Enrolled: {info.get('enrolled_date', 'Unknown')}")
        print("-" * 50)
    
    total_count = student_count + staff_count
    if total_count == 0:
        print("📁 No users enrolled.")
    else:
        print(f"\n📊 Total Users: {total_count}")
        print(f"   🎓 Students: {student_count}")
        print(f"   👔 Staff: {staff_count}")
        
def admin_delete_fingerprint():
    """Delete user fingerprint"""
    database = load_fingerprint_database()
    if not database:
        print("📁 No users enrolled.")
        return
    
    admin_view_enrolled()
    
    try:
        finger_id = get_user_input("Enter Slot ID to delete")
        
        if finger_id == "1":
            print("❌ Cannot delete admin slot. Use 'Change Admin' option.")
            return
            
        if finger_id not in database:
            print("❌ Slot not found.")
            return
            
        user_info = database[finger_id]
        user_type = user_info.get('user_type', 'STUDENT')
        user_id = user_info.get('student_id' if user_type == 'STUDENT' else 'staff_no', 'N/A')
        
        print(f"\n📋 Deleting: {user_info['name']} ({user_type} - ID: {user_id})")
        
        if confirm_action(f"Delete {user_info['name']}?", dangerous=True):
            if finger.delete_model(int(finger_id)) == adafruit_fingerprint.OK:
                del database[finger_id]
                save_fingerprint_database(database)
                print(f"✅ Deleted {user_info['name']}")
            else:
                print("❌ Failed to delete from sensor.")
        else:
            print("❌ Cancelled.")
            
    except ValueError:
        print("❌ Invalid slot ID.")
        
def admin_reset_all():
    """Reset all system data with confirmation"""
    if not confirm_action("Delete ALL student fingerprints?", dangerous=True):
        print("❌ Cancelled.")
        return
        
    if input("⚠️ Type 'DELETE ALL' to confirm: ").strip() != 'DELETE ALL':
        print("❌ Cancelled.")
        return
    
    try:
        if finger.empty_library() == adafruit_fingerprint.OK:
            save_fingerprint_database({})
            print("✅ All student fingerprint data has been reset.")
        else:
            print("❌ Failed to clear sensor database.")

        database = load_fingerprint_database()
        
        # Delete all student fingerprints (preserve admin)
        for slot_id in list(database.keys()):
            if slot_id != "1":
                finger.delete_model(int(slot_id))
        
        save_fingerprint_database({})
        print("✅ All student data reset. Admin preserved.")
        
    except Exception as e:
        print(f"❌ Reset error: {e}")

def admin_sync_database():
    """Sync database from Google Sheets - saves directly to motorpass.db"""
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        import sqlite3
        from datetime import datetime
        
        print("🔄 Starting database sync from Google Sheets...")
        
        # Google Sheets authentication
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("json_folder/credentials.json", scope)
        client = gspread.authorize(creds)
        
        # Open the spreadsheet
        sheet_name = "MotorPass Registration Form (Responses)"
        print(f"📊 Connecting to '{sheet_name}'...")
        
        sheet = client.open(sheet_name).sheet1
        rows = sheet.get_all_records()
        
        print(f"📋 Found {len(rows)} records in Google Sheets")
        
        # Connect to motorpass.db
        conn = sqlite3.connect("database/motorpass.db")
        cursor = conn.cursor()
        
        students_added = 0
        staff_added = 0
        errors = 0
        
        print("💾 Saving to motorpass.db...")
        
        for row in rows:
            try:
                # Extract data from row
                full_name = row.get('Full Name', '').strip()
                license_number = row.get('License Number', '').strip()
                expiration_date = row.get('License Expiration Date', '').strip()
                plate_number = row.get('Plate Number of the Motorcycle', '').strip()
                course = row.get('Course', '').strip()
                student_id = row.get('Student No.', '').strip()
                staff_role = row.get('Staff Role', '').strip()
                staff_no = row.get('Staff No.', '').strip()
                
                # Skip if no name
                if not full_name:
                    continue
                
                # Determine if student or staff
                if student_id and not staff_no:
                    # It's a student
                    cursor.execute('''
                        INSERT OR REPLACE INTO students 
                        (student_id, full_name, course, license_number, 
                         license_expiration, plate_number, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (student_id, full_name, course, license_number, 
                          expiration_date, plate_number))
                    students_added += 1
                    
                elif staff_no and not student_id:
                    # It's a staff member
                    cursor.execute('''
                        INSERT OR REPLACE INTO staff 
                        (staff_no, full_name, staff_role, license_number, 
                         license_expiration, plate_number, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (staff_no, full_name, staff_role, license_number, 
                          expiration_date, plate_number))
                    staff_added += 1
                    
                elif student_id and staff_no:
                    # Both filled - handle as student by default
                    print(f"⚠️ Both Student No. and Staff No. filled for {full_name}, treating as student")
                    cursor.execute('''
                        INSERT OR REPLACE INTO students 
                        (student_id, full_name, course, license_number, 
                         license_expiration, plate_number, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (student_id, full_name, course, license_number, 
                          expiration_date, plate_number))
                    students_added += 1
                else:
                    # Neither student nor staff ID
                    print(f"⚠️ Skipping {full_name} - No Student No. or Staff No.")
                    errors += 1
                    
            except Exception as e:
                print(f"❌ Error processing row for {row.get('Full Name', 'Unknown')}: {e}")
                errors += 1
        
        # Commit all changes
        conn.commit()
        
        # Get final counts
        cursor.execute('SELECT COUNT(*) FROM students')
        total_students = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM staff')
        total_staff = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n✅ Database sync completed!")
        print(f"📊 Sync Results:")
        print(f"   🎓 Students added/updated: {students_added}")
        print(f"   👔 Staff added/updated: {staff_added}")
        if errors > 0:
            print(f"   ❌ Errors: {errors}")
        
        print(f"\n📊 Database Totals:")
        print(f"   🎓 Total Students: {total_students}")
        print(f"   👔 Total Staff: {total_staff}")
            
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"❌ Spreadsheet '{sheet_name}' not found")
        print("💡 Please check:")
        print("   1. The exact name of your Google Sheet")
        print("   2. That the service account has access to the sheet")
        print("   3. The sheet is shared with the service account email")
        
    except FileNotFoundError:
        print("❌ credentials.json not found!")
        print("💡 Please ensure json_folder/credentials.json exists")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        print("💡 Check your credentials.json and internet connection")
                    
def admin_view_time_records():
    """View all time records with user type information"""
    records = get_all_time_records()
    if not records:
        print("📁 No time records.")
        return
    
    print("\n🕒 TIME RECORDS:")
    display_separator()
    
    for record in records:
        status_icon = "🟢" if record['status'] == 'IN' else "🔴"
        user_type_icon = "🎓" if record.get('user_type', 'STUDENT') == 'STUDENT' else "👔"
        
        print(f"{status_icon} {user_type_icon} {record['student_name']} ({record['student_id']})")
        print(f"   📅 {record['date']} 🕒 {record['time']} 📊 {record['status']}")
        print("-" * 50)

def admin_clear_time_records():
    """Clear all time records"""
    if not confirm_action("Clear ALL time records?", dangerous=True):
        print("❌ Cancelled.")
        return
    
    if clear_all_time_records():
        print("✅ All time records cleared.")
    else:
        print("❌ Failed to clear records.")


def admin_change_fingerprint():
    """Change admin fingerprint (hidden option)"""
    print("\n🔄 CHANGE ADMIN FINGERPRINT")
    print("⚠️  This will replace the current admin fingerprint")
    
    if not confirm_action("Replace admin fingerprint?", dangerous=True):
        print("❌ Cancelled.")
        return
    
    if enroll_admin_fingerprint():
        print("✅ Admin fingerprint changed!")
    else:
        print("❌ Failed to change.")

# =================== MAIN ADMIN PANEL ===================

def admin_panel():
    """Secured admin panel with fingerprint authentication"""
    
    # Check if admin fingerprint exists
    if not check_admin_fingerprint_exists():
        print("\n🔐 NO ADMIN FINGERPRINT FOUND!")
        print("⚠️  First-time setup required")
        
        if input("\nProceed with admin enrollment? (y/N): ").lower() != 'y':
            print("❌ Access cancelled.")
            return
        
        if not enroll_admin_fingerprint():
            print("❌ Enrollment failed. Cannot access admin panel.")
            return
        
        print("\n✅ Admin enrolled! You can now access admin panel.")
        input("Press Enter to continue...")
    
    # Authenticate admin
    print("\n🔐 ADMIN PANEL ACCESS")
    
    if not authenticate_admin():
        print("❌ Authentication failed! Access denied.")
        return
    
    print("✅ Welcome to admin panel!")
    
    # Admin panel loop
    while True:
        display_menu(ADMIN_MENU)
        choice = get_user_input("Select option")
        
        actions = {
            "1": admin_enroll,
            "2": admin_view_enrolled,
            "3": admin_delete_fingerprint,
            "4": admin_reset_all,
            "5": admin_sync_database,
            "6": admin_view_time_records,
            "7": admin_clear_time_records,
            "0": admin_change_fingerprint  # Hidden option
        }
        
        if choice in actions:
            actions[choice]()
        elif choice == "8":
            break
        else:
            print("❌ Invalid option. Please try again.")
            print("❌ Invalid option.")
