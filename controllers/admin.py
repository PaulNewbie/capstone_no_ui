# controllers/admin.py - Updated with Automated Slot Assignment

from config import ADMIN_MENU
from services.fingerprint import *

from database.db_operations import (
    get_all_time_records,
    clear_all_time_records,
    get_students_currently_in,
    get_database_stats,
    backup_databases
)

# Import unified database for sync
from database.unified_db import db

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
    """Enroll new student with automatic slot assignment"""
    if finger.read_templates() != adafruit_fingerprint.OK:
        print("❌ Failed to read templates")
        return
    
    print(f"📊 Current enrollments: {finger.template_count}")
    print("🤖 Auto-assigning next available slot...")
    
    # Automatically enroll with next available slot
    success = enroll_finger_with_student_info()
    print(f"{'✅ Enrollment complete!' if success else '❌ Enrollment failed.'}")

def admin_view_enrolled():
    """Display all enrolled students from UNIFIED database"""
    students = db.get_all_students()
    
    if not students:
        print("📁 No students enrolled.")
        return
    
    print("\n👥 ENROLLED STUDENTS:")
    display_separator()
    
    for student in students:
        print(f"🆔 Slot: {student.get('fingerprint_slot', 'N/A')}")
        print(f"👤 Name: {student['full_name']}")
        print(f"🎓 Student ID: {student['student_id']}")
        print(f"📚 Course: {student.get('course', 'N/A')}")
        print(f"🪪 License: {student.get('license_number', 'N/A')}")
        print(f"📅 License Exp: {student.get('license_expiration', 'N/A')}")
        print(f"🕒 Enrolled: {student.get('created_at', 'Unknown')}")
        print("-" * 50)
    
    print(f"\n📊 Total Students: {len(students)}")

def admin_delete_fingerprint():
    """Delete student fingerprint"""
    # Get from both JSON (for fingerprint) and unified DB (for display)
    json_database = load_fingerprint_database()
    db_students = db.get_all_students()
    
    if not db_students:
        print("📁 No students enrolled.")
        return
    
    admin_view_enrolled()
    
    try:
        finger_id = get_user_input("Enter Fingerprint Slot ID to delete")
        
        if finger_id == "1":
            print("❌ Cannot delete admin slot. Use 'Change Admin' option.")
            return
            
        # Find student in unified DB
        student = None
        for s in db_students:
            if str(s.get('fingerprint_slot')) == finger_id:
                student = s
                break
        
        if not student:
            print("❌ Slot not found.")
            return
            
        print(f"\n📋 Deleting: {student['full_name']} (ID: {student['student_id']})")
        
        if confirm_action(f"Delete {student['full_name']}?", dangerous=True):
            # Delete from fingerprint sensor
            if finger.delete_model(int(finger_id)) == adafruit_fingerprint.OK:
                # Update unified database (set fingerprint_slot to null)
                db.update_student(student['student_id'], fingerprint_slot=None)
                
                # Remove from JSON database
                if finger_id in json_database:
                    del json_database[finger_id]
                    save_fingerprint_database(json_database)
                
                print(f"✅ Deleted {student['full_name']}")
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
        # Clear fingerprint sensor
        if finger.empty_library() == adafruit_fingerprint.OK:
            print("✅ Fingerprint sensor cleared.")
        else:
            print("❌ Failed to clear sensor database.")

        # Clear JSON database
        save_fingerprint_database({})
        
        # Clear unified database (but preserve students, just remove fingerprint associations)
        students = db.get_all_students()
        for student in students:
            db.update_student(student['student_id'], fingerprint_slot=None)
        
        print("✅ All fingerprint associations reset. Student data preserved.")
        
    except Exception as e:
        print(f"❌ Reset error: {e}")

def admin_sync_database():
    """Sync database from Google Sheets to UNIFIED database"""
    print("\n☁️  GOOGLE SHEETS SYNC TO UNIFIED DATABASE")
    print("="*50)
    
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        from datetime import datetime
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("json_folder/credentials.json", scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("MotorPass (Responses)").sheet1
        rows = sheet.get_all_records()
        
        print(f"📥 Found {len(rows)} records in Google Sheets")
        
        synced_count = 0
        updated_count = 0
        
        for row in rows:
            try:
                student_id = row.get('Student No.', f'GS_{synced_count}')
                full_name = row.get('Full Name', 'Unknown')
                course = row.get('Course', None)
                license_number = row.get('License Number', None)
                license_expiration = row.get('License Expiration Date', None)
                
                # Check if student already exists
                existing = db.get_student(student_id=student_id)
                
                if existing:
                    # Update existing student with Google Sheets data
                    db.update_student(
                        student_id=student_id,
                        full_name=full_name,
                        course=course,
                        license_number=license_number,
                        license_expiration=license_expiration
                    )
                    print(f"  🔄 Updated: {full_name}")
                    updated_count += 1
                else:
                    # Add new student
                    success = db.add_student(
                        student_id=student_id,
                        full_name=full_name,
                        course=course,
                        license_number=license_number,
                        license_expiration=license_expiration
                    )
                    
                    if success:
                        print(f"  ✅ Added: {full_name}")
                        synced_count += 1
                        
            except Exception as e:
                print(f"  ❌ Error processing row: {e}")
        
        print(f"\n📊 SYNC COMPLETE:")
        print(f"  New students: {synced_count}")
        print(f"  Updated students: {updated_count}")
        print(f"  Total in database: {len(db.get_all_students())}")
        
    except ImportError:
        print("❌ Google Sheets libraries not installed")
        print("  Install with: pip install gspread oauth2client")
    except FileNotFoundError:
        print("❌ Google credentials not found: json_folder/credentials.json")
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

def admin_show_sync_status():
    """Show sync status between different systems"""
    print("\n📊 SYSTEM SYNC STATUS")
    print("="*50)
    
    # Check JSON fingerprint database
    json_file = "json_folder/fingerprint_database.json"
    json_count = 0
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            json_count = len([k for k in json_data.keys() if k != "1"])  # Exclude admin
        except:
            pass
    
    # Check unified database
    db_students = db.get_all_students()
    db_count = len(db_students)
    
    # Check fingerprint associations
    associated_count = len([s for s in db_students if s.get('fingerprint_slot')])
    
    # Check available slots
    available_slots = []
    try:
        for slot in range(2, finger.library_size):
            if finger.load_model(slot) != adafruit_fingerprint.OK:
                available_slots.append(slot)
    except:
        pass
    
    print(f"📄 JSON Fingerprint Database: {json_count} students")
    print(f"🗄️  Unified Database: {db_count} students")
    print(f"🔗 With Fingerprint Association: {associated_count} students")
    print(f"📍 Available Slots: {len(available_slots)} slots")
    print(f"   Next available: {available_slots[0] if available_slots else 'None'}")
    
    if json_count != associated_count:
        print(f"\n⚠️  SYNC NEEDED: {abs(json_count - associated_count)} students not synchronized")
        print("   Run: python sync_all_data.py")
    else:
        print(f"\n✅ All systems synchronized!")

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
            "0": admin_change_fingerprint,  # Hidden option
            "9": admin_show_sync_status      # Hidden sync status
        }
        
        if choice in actions:
            actions[choice]()
        elif choice == "8":
            break
        else:
            print("❌ Invalid option. Try '9' for sync status.")
