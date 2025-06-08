from config import ADMIN_MENU
from services.fingerprint import *
from services.time_tracker import *
from database.db_operations import *
from utils.display_helpers import display_menu, get_user_input, confirm_action, display_separator, get_num

import time

def admin_enroll():
    """Enroll new student with fingerprint authentication"""
    if finger.read_templates() != adafruit_fingerprint.OK:
        print("❌ Failed to read fingerprint templates")
        return
    
    print(f"📊 Current enrollments: {finger.template_count}")
    location = get_num(finger.library_size)
    success = enroll_finger_with_student_info(location)
    print(f"Student enrollment {'✅ completed successfully!' if success else '❌ failed.'}")

def admin_view_enrolled():
    """Display all enrolled students with their information"""
    database = load_fingerprint_database()
    if not database:
        print("📁 No students enrolled in the system.")
        return
    
    print("\n👥 ENROLLED STUDENTS:")
    display_separator()
    
    for finger_id, info in database.items():
        student_data = [
            f"🆔 Slot: {finger_id}",
            f"👤 Name: {info['name']}",
            f"🎓 Student ID: {info.get('student_id', 'N/A')}",
            f"📚 Course: {info.get('course', 'N/A')}",
            f"🪪 License: {info.get('license_number', 'N/A')}",
            f"📅 License Exp: {info.get('license_expiration', 'N/A')}",
            f"🕒 Enrolled: {info.get('enrolled_date', 'Unknown')}"
        ]
        for line in student_data:
            print(line)
        print("-" * 50)

def admin_delete_fingerprint():
    """Delete student fingerprint from system"""
    database = load_fingerprint_database()
    if not database:
        print("📁 No students enrolled in the system.")
        return
    
    admin_view_enrolled()
    
    try:
        finger_id = get_user_input("Enter Fingerprint Slot ID to delete")
        if finger_id not in database:
            print("❌ Fingerprint slot ID not found.")
            return
            
        student_info = database[finger_id]
        print(f"\n📋 Deleting: {student_info['name']} (ID: {student_info.get('student_id', 'N/A')})")
        
        if confirm_action(f"Delete {student_info['name']}?", dangerous=True):
            if finger.delete_model(int(finger_id)) == adafruit_fingerprint.OK:
                del database[finger_id]
                save_fingerprint_database(database)
                print(f"✅ Successfully deleted {student_info['name']}")
            else:
                print("❌ Failed to delete fingerprint from sensor.")
        else:
            print("❌ Deletion cancelled.")
            
    except ValueError:
        print("❌ Invalid fingerprint slot ID.")

def admin_reset_all():
    """Reset all system data with double confirmation"""
    if not confirm_action("Delete ALL enrolled student fingerprints?", dangerous=True):
        print("❌ Reset cancelled.")
        return
        
    if input("⚠️ Type 'DELETE ALL' to confirm: ").strip() != 'DELETE ALL':
        print("❌ Reset cancelled.")
        return
    
    try:
        if finger.empty_library() == adafruit_fingerprint.OK:
            save_fingerprint_database({})
            print("✅ All student fingerprint data has been reset.")
        else:
            print("❌ Failed to clear sensor database.")
    except Exception as e:
        print(f"❌ Error occurred during reset: {e}")

def admin_sync_database():
    """Sync student database from Google Sheets"""
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
        
        conn = sqlite3.connect("students.db")
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
        print(f"✅ Database sync completed! Synced {len(rows)} records.")
        
    except Exception as e:
        print(f"❌ Database sync failed: {e}")

def admin_view_time_records():
    """View all student time in/out records"""
    records = get_all_time_records()
    if not records:
        print("📁 No time records found.")
        return
    
    print("\n🕒 TIME IN/OUT RECORDS:")
    display_separator()
    
    for record in records:
        status_icon = "🟢" if record['status'] == 'IN' else "🔴"
        print(f"{status_icon} {record['student_name']} ({record['student_id']})")
        print(f"   📅 Date: {record['date']}")
        print(f"   🕒 Time: {record['time']}")
        print(f"   📊 Status: {record['status']}")
        print("-" * 50)

def admin_clear_time_records():
    """Clear all time records with confirmation"""
    if not confirm_action("Clear ALL time records?", dangerous=True):
        print("❌ Clear operation cancelled.")
        return
    
    if clear_all_time_records():
        print("✅ All time records have been cleared.")
    else:
        print("❌ Failed to clear time records.")

def admin_panel():
    """Main admin panel controller"""
    while True:
        display_menu(ADMIN_MENU)
        choice = get_user_input("Select admin option")
        
        actions = {
            "1": admin_enroll,
            "2": admin_view_enrolled,
            "3": admin_delete_fingerprint,
            "4": admin_reset_all,
            "5": admin_sync_database,
            "6": admin_view_time_records,
            "7": admin_clear_time_records
        }
        
        if choice in actions:
            actions[choice]()
        elif choice == "8":
            break
        else:
            print("❌ Invalid option. Please try again.")
