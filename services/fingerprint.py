# services/fingerprint.py - Cleaned Fingerprint Service

import time
import serial
import adafruit_fingerprint
import json
import os
import tkinter as tk
from tkinter import simpledialog, messagebox

# Import database operations
from database.db_operations import (
    get_student_by_id,
    get_student_time_status,
    record_time_in,
    record_time_out,
    record_time_attendance,
    get_all_time_records,
    clear_all_time_records,
    get_students_currently_in
)

# =================== SETUP ===================
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# File paths
FINGERPRINT_DATA_FILE = "json_folder/fingerprint_database.json"

# =================== JSON DATABASE FUNCTIONS ===================

def load_fingerprint_database():
    """Load fingerprint database"""
    if os.path.exists(FINGERPRINT_DATA_FILE):
        try:
            with open(FINGERPRINT_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_fingerprint_database(database):
    """Save fingerprint database"""
    os.makedirs(os.path.dirname(FINGERPRINT_DATA_FILE), exist_ok=True)
    with open(FINGERPRINT_DATA_FILE, 'w') as f:
        json.dump(database, f, indent=4)

def load_admin_database():
    """Load admin database"""
    admin_file = "json_folder/admin_database.json"
    if os.path.exists(admin_file):
        try:
            with open(admin_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

# =================== GUI FUNCTIONS ===================

def get_student_id_gui():
    """Get student ID via GUI and fetch info"""
    root = tk.Tk()
    root.withdraw()
    
    while True:
        student_id = simpledialog.askstring("Student Enrollment", "Enter Student Number:")
        
        if not student_id:
            root.destroy()
            return None
        
        student_id = student_id.strip()
        student_info = get_student_by_id(student_id)
        
        if student_info:
            confirmation_message = f"""
Student Information Found:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {student_info['full_name']}
🆔 Student No.: {student_info['student_id']}
📚 Course: {student_info['course']}
🪪 License No.: {student_info['license_number']}
📅 License Exp.: {student_info['expiration_date']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Proceed with fingerprint enrollment?
            """
            
            if messagebox.askyesno("Confirm Student Information", confirmation_message):
                root.destroy()
                return student_info
        else:
            if not messagebox.askyesno("Student Not Found", 
                f"Student ID '{student_id}' not found.\n\nTry again?"):
                root.destroy()
                return None

def show_message_gui(title, message):
    """Show message dialog"""
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, message)
    root.destroy()

def display_student_info(student_info):
    """Display student info in console"""
    print(f"\n{'='*50}")
    print("📋 STUDENT INFORMATION")
    print(f"{'='*50}")
    print(f"👤 Name: {student_info['full_name']}")
    print(f"🆔 Student No.: {student_info['student_id']}")
    print(f"📚 Course: {student_info['course']}")
    print(f"🪪 License: {student_info['license_number']}")
    print(f"📅 Expiration: {student_info['expiration_date']}")
    print(f"{'='*50}")

# =================== FINGERPRINT HELPER FUNCTIONS ===================

def _capture_fingerprint_image(attempt_num, max_attempts=5):
    """Helper function to capture fingerprint image with retry logic"""
    print(f"👆 Place finger on sensor - Attempt {attempt_num}/{max_attempts}...")
    
    # Wait for finger with timeout
    finger_detected = False
    for _ in range(100):  # 10 second timeout
        if finger.get_image() == adafruit_fingerprint.OK:
            finger_detected = True
            break
        time.sleep(0.1)
        print(".", end="")
    
    if not finger_detected:
        print("\n⏰ Timeout waiting for finger")
        return False
    
    print("✅ Finger detected!")
    return True

def _process_fingerprint_template(template_num):
    """Helper function to process fingerprint template"""
    print("🔄 Processing...", end="")
    if finger.image_2_tz(template_num) != adafruit_fingerprint.OK:
        print("❌ Failed to process")
        return False
    print("✅")
    return True

# =================== FINGERPRINT FUNCTIONS ===================

def enroll_finger_with_student_info(location):
    """Enhanced enrollment using Student ID with retry mechanism"""
    print(f"\n🔒 Starting enrollment for slot #{location}")
    
    student_info = get_student_id_gui()
    if not student_info:
        print("❌ No student selected.")
        return False
    
    display_student_info(student_info)
    print(f"👤 Enrolling: {student_info['full_name']}")
    
    # Fingerprint enrollment process with retry
    for fingerimg in range(1, 3):
        max_attempts = 5
        success = False
        
        for attempt in range(1, max_attempts + 1):
            if _capture_fingerprint_image(attempt, max_attempts):
                if _process_fingerprint_template(fingerimg):
                    success = True
                    break
            
            if attempt < max_attempts:
                retry = input("Try again? (y/n): ").lower() == 'y'
                if not retry:
                    print("❌ Enrollment cancelled")
                    return False
        
        if not success:
            print("❌ Failed to capture fingerprint after maximum attempts")
            return False
        
        if fingerimg == 1:
            print("✋ Remove finger and wait...")
            time.sleep(2)
            while finger.get_image() != adafruit_fingerprint.NOFINGER:
                time.sleep(0.1)
            print("✅ Ready for second capture")

    print("🗝️ Creating fingerprint model...", end="")
    if finger.create_model() != adafruit_fingerprint.OK:
        print("❌ Failed to create model")
        return False
    print("✅")

    print(f"💾 Storing model #{location}...", end="")
    if finger.store_model(location) == adafruit_fingerprint.OK:
        print("✅")
        
        # Save student info
        database = load_fingerprint_database()
        database[str(location)] = {
            "name": student_info['full_name'],
            "student_id": student_info['student_id'],
            "course": student_info['course'],
            "license_number": student_info['license_number'],
            "license_expiration": student_info['expiration_date'],
            "enrolled_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_fingerprint_database(database)
        
        print(f"🎉 Successfully enrolled {student_info['full_name']} at slot #{location}")
        
        success_message = f"""
Enrollment Successful! ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Student: {student_info['full_name']}
🆔 Student No.: {student_info['student_id']}
📚 Course: {student_info['course']}
🪪 License: {student_info['license_number']}
🔒 Fingerprint Slot: #{location}
📅 Enrolled: {time.strftime("%Y-%m-%d %H:%M:%S")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        show_message_gui("Enrollment Complete", success_message)
        return True
    else:
        print("❌ Storage failed")
        return False

def authenticate_fingerprint(max_attempts=3):
    """Authenticate fingerprint and return student info with retry mechanism"""
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        print(f"\n🔒 Fingerprint Authentication (Attempt {attempts}/{max_attempts})")
        print("👆 Place finger on sensor...")
        
        # Wait for finger placement
        while finger.get_image() != adafruit_fingerprint.OK:
            pass
        
        print("🔄 Processing...")
        if finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("❌ Failed to process fingerprint image")
            if attempts < max_attempts:
                print("🔄 Please try again...")
                time.sleep(1)
                continue
            else:
                print("❌ Maximum attempts reached. Authentication failed.")
                return None
        
        print("🔍 Searching...")
        if finger.finger_search() != adafruit_fingerprint.OK:
            print("❌ No fingerprint match found")
            
            if attempts < max_attempts:
                print(f"🔄 Try again? ({max_attempts - attempts} attempts remaining)")
                choice = input("Press Enter to retry, or 'q' to quit: ").strip().lower()
                if choice == 'q':
                    print("❌ Authentication cancelled by user")
                    return None
                continue
            else:
                print("❌ Maximum attempts reached. No match found.")
                return None
        
        # Authentication successful - get student info
        database = load_fingerprint_database()
        finger_id = str(finger.finger_id)
        
        if finger_id in database:
            student_info = database[finger_id]
            print(f"✅ Authentication successful!")
            print(f"👤 Welcome: {student_info['name']}")
            print(f"🆔 ID: {student_info.get('student_id', 'N/A')}")
            print(f"📚 Course: {student_info.get('course', 'N/A')}")
            print(f"🎯 Confidence: {finger.confidence}")
            
            return {
                "name": student_info['name'],
                "student_id": student_info.get('student_id', 'N/A'),
                "course": student_info.get('course', 'N/A'),
                "license_number": student_info.get('license_number', 'N/A'),
                "license_expiration": student_info.get('license_expiration', 'N/A'),
                "finger_id": finger.finger_id,
                "confidence": finger.confidence,
                "enrolled_date": student_info.get('enrolled_date', 'Unknown')
            }
        else:
            print(f"⚠️ Fingerprint recognized (ID: {finger.finger_id}) but no student data found")
            return {
                "name": f"Unknown User (ID: {finger.finger_id})",
                "student_id": "N/A",
                "course": "N/A",
                "license_number": "N/A",
                "license_expiration": "N/A",
                "finger_id": finger.finger_id,
                "confidence": finger.confidence,
                "enrolled_date": "Unknown"
            }
    
    return None

def authenticate_admin(max_attempts=3):
    """Authenticate admin using fingerprint with retry mechanism"""
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        print(f"\n🔐 ADMIN AUTHENTICATION (Attempt {attempts}/{max_attempts})")
        print("👆 Place admin finger on sensor...")
        
        # Wait for finger and process
        while finger.get_image() != adafruit_fingerprint.OK:
            print(".", end="")
            time.sleep(0.1)
        
        print("\n🔄 Processing...")
        if finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("❌ Failed to process fingerprint")
            if attempts < max_attempts:
                print("🔄 Please try again...")
                time.sleep(1)
                continue
            else:
                print("❌ Maximum attempts reached. Authentication failed.")
                return False
        
        print("🔍 Searching...")
        if finger.finger_search() != adafruit_fingerprint.OK:
            print("❌ No match found")
            if attempts < max_attempts:
                print(f"🔄 Try again? ({max_attempts - attempts} attempts remaining)")
                choice = input("Press Enter to retry, or 'q' to quit: ").strip().lower()
                if choice == 'q':
                    print("❌ Admin authentication cancelled")
                    return False
                continue
            else:
                print("❌ Maximum attempts reached. Access denied.")
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
            if attempts < max_attempts:
                print(f"🔄 Please use admin fingerprint. Try again? ({max_attempts - attempts} attempts remaining)")
                choice = input("Press Enter to retry, or 'q' to quit: ").strip().lower()
                if choice == 'q':
                    print("❌ Admin authentication cancelled")
                    return False
                continue
            else:
                print("❌ Maximum attempts reached. Access denied.")
                return False
    
    return False

def authenticate_fingerprint_with_time_tracking():
    """Authenticate fingerprint and auto handle time in/out"""
    student_info = authenticate_fingerprint()
    
    if not student_info or student_info['student_id'] == 'N/A':
        return student_info
    
    time_status = record_time_attendance(student_info)
    print(f"🕒 {time_status}")
    
    return student_info

def authenticate_fingerprint_custom_retry(max_attempts=3):
    """Authenticate fingerprint with custom retry count"""
    return authenticate_fingerprint(max_attempts)

# =================== LEGACY SUPPORT ===================

def enroll_finger_with_name(location):
    """Legacy function - redirects to new enrollment"""
    print("⚠️ Using legacy enrollment. Consider using enroll_finger_with_student_info().")
    return enroll_finger_with_student_info(location)
