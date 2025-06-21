# controllers/admin.py 

from config import ADMIN_MENU
from services.fingerprint import *

from dashboard.database.db_operations import (
    get_all_time_records,
    clear_all_time_records,
    get_students_currently_in,
    get_database_stats,
    backup_databases
)

from utils.display_helpers import (
	display_menu, 
	get_user_input, 
	confirm_action, 
	display_separator, 
	get_num 
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
    """Enroll new student"""
    if finger.read_templates() != adafruit_fingerprint.OK:
        print("❌ Failed to read templates")
        return
    
    print(f"📊 Current enrollments: {finger.template_count}")

    # Get slot (skip admin slot 1)
    location = get_num(finger.library_size)
    if location == 1:
        print("❌ Slot #1 reserved for admin. Use slot 2+")
        return
    
    success = enroll_finger_with_student_info(location)
    print(f"{'✅ Success!' if success else '❌ Failed.'}")

def admin_view_enrolled():
    """Display all enrolled students"""
    database = load_fingerprint_database()
    if not database:
        print("📁 No students enrolled.")
        return
    
    print("\n👥 ENROLLED STUDENTS:")
    display_separator()
    
    student_count = 0  # Initialize student_count
    
    for finger_id, info in database.items():
        # Skip admin slot
        if finger_id == "1":
            continue
            
        student_count += 1
        
        print(f"🆔 Slot: {finger_id}")
        print(f"👤 Name: {info['name']}")
        print(f"🎓 Student ID: {info.get('student_id', 'N/A')}")
        print(f"📚 Course: {info.get('course', 'N/A')}")
        print(f"🪪 License: {info.get('license_number', 'N/A')}")
        print(f"📅 License Exp: {info.get('license_expiration', 'N/A')}")
        print(f"🕒 Enrolled: {info.get('enrolled_date', 'Unknown')}")
        print("-" * 50)
    
    if student_count == 0:
        print("📁 No students enrolled.")
    else:
        print(f"\n📊 Total Students: {student_count}")

def admin_delete_fingerprint():
    """Delete student fingerprint"""
    database = load_fingerprint_database()
    if not database:
        print("📁 No students enrolled.")
        return
    
    admin_view_enrolled()
    
    try:
        finger_id = get_user_input("Enter Fingerprint Slot ID to delete")
        finger_id = get_user_input("Enter Slot ID to delete")
        
        if finger_id == "1":
            print("❌ Cannot delete admin slot. Use 'Change Admin' option.")
            return
            
        if finger_id not in database:
            print("❌ Slot not found.")
            return
            
        student_info = database[finger_id]
        print(f"\n📋 Deleting: {student_info['name']} (ID: {student_info.get('student_id', 'N/A')})")
        
        if confirm_action(f"Delete {student_info['name']}?", dangerous=True):
            if finger.delete_model(int(finger_id)) == adafruit_fingerprint.OK:
                del database[finger_id]
                save_fingerprint_database(database)
                print(f"✅ Deleted {student_info['name']}")
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
    """Sync database from Google Sheets"""
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        import sqlite3
        from datetime import datetime
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("json_folder/credentials.json", scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("MotorPass (Responses)").sheet1
        rows = sheet.get_all_records()
        
        conn = sqlite3.connect("database/students.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                license_number TEXT,
                expiration_date TEXT,
                course TEXT,
                student_id TEXT UNIQUE,
                synced_at TEXT
            )
        ''')
        
        cursor.execute("DELETE FROM students")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for row in rows:
            cursor.execute('''
                INSERT INTO students (full_name, license_number, expiration_date, course, student_id, synced_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (row['Full Name'], row['License Number'], row['License Expiration Date'],
                  row['Course'], row['Student No.'], current_time))
        
        conn.commit()
        conn.close()
        print(f"✅ Synced {len(rows)} records.")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")

def admin_view_time_records():
    """View all time records"""
    records = get_all_time_records()
    if not records:
        print("📁 No time records.")
        return
    
    print("\n🕒 TIME RECORDS:")
    display_separator()
    
    for record in records:
        status_icon = "🟢" if record['status'] == 'IN' else "🔴"
        print(f"{status_icon} {record['student_name']} ({record['student_id']})")
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
