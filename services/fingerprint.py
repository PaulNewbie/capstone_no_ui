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
    get_user_by_id,
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

def get_user_id_gui():
    """Get user ID via GUI and fetch info (works for both students and staff)"""
    root = tk.Tk()
    root.withdraw()
    
    while True:
        user_id = simpledialog.askstring("User Enrollment", 
                                        "Enter Student No. or Staff No.:")
        
        if not user_id:
            root.destroy()
            return None
        
        user_id = user_id.strip()
        user_info = get_user_by_id(user_id)  # This function now handles both types
        
        if user_info:
            # Determine display information based on user type
            if user_info['user_type'] == 'STUDENT':
                confirmation_message = f"""
Student Information Found:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {user_info['full_name']}
🆔 Student No.: {user_info['student_id']}
📚 Course: {user_info['course']}
🪪 License No.: {user_info['license_number']}
📅 License Exp.: {user_info['expiration_date']}
🏍️ Plate No.: {user_info['plate_number']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Proceed with fingerprint enrollment?
            """
            else:  # STAFF
                confirmation_message = f"""
Staff Information Found:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {user_info['full_name']}
🆔 Staff No.: {user_info['staff_no']}
👔 Role: {user_info['staff_role']}
🪪 License No.: {user_info['license_number']}
📅 License Exp.: {user_info['expiration_date']}
🏍️ Plate No.: {user_info['plate_number']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Proceed with fingerprint enrollment?
            """
            
            if messagebox.askyesno("Confirm User Information", confirmation_message):
                root.destroy()
                return user_info
        else:
            if not messagebox.askyesno("User Not Found", 
                f"User ID '{user_id}' not found.\n\nTry again?"):
                root.destroy()
                return None
                
def show_message_gui(title, message):
    """Show message dialog"""
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, message)
    root.destroy()

def display_user_info(user_info):
    """Display user info in console (works for both students and staff)"""
    print(f"\n{'='*50}")
    if user_info['user_type'] == 'STUDENT':
        print("📋 STUDENT INFORMATION")
        print(f"{'='*50}")
        print(f"👤 Name: {user_info['full_name']}")
        print(f"🆔 Student No.: {user_info['student_id']}")
        print(f"📚 Course: {user_info['course']}")
        print(f"🪪 License: {user_info['license_number']}")
        print(f"📅 Expiration: {user_info['expiration_date']}")
        print(f"🏍️ Plate: {user_info['plate_number']}")
    else:  # STAFF
        print("📋 STAFF INFORMATION")
        print(f"{'='*50}")
        print(f"👤 Name: {user_info['full_name']}")
        print(f"🆔 Staff No.: {user_info['staff_no']}")
        print(f"👔 Role: {user_info['staff_role']}")
        print(f"🪪 License: {user_info['license_number']}")
        print(f"📅 Expiration: {user_info['expiration_date']}")
        print(f"🏍️ Plate: {user_info['plate_number']}")
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

def enroll_finger_with_user_info(location):
    """Enhanced enrollment using Student ID or Staff No with retry mechanism"""
    print(f"\n🔒 Starting enrollment for slot #{location}")
    
    user_info = get_user_id_gui()  # Updated function name
    if not user_info:
        print("❌ No user selected.")
        return False
    
    display_user_info(user_info)  # Updated function name
    print(f"👤 Enrolling: {user_info['full_name']} ({user_info['user_type']})")
    
    # Fingerprint enrollment process with retry (same as before)
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
        
        # Save user info to fingerprint database
        database = load_fingerprint_database()
        database[str(location)] = {
            "name": user_info['full_name'],
            "user_type": user_info['user_type'],
            "student_id": user_info.get('student_id', ''),
            "staff_no": user_info.get('staff_no', ''),
            "unified_id": user_info['unified_id'],  # For time tracking
            "course": user_info.get('course', ''),
            "staff_role": user_info.get('staff_role', ''),
            "license_number": user_info['license_number'],
            "license_expiration": user_info['expiration_date'],
            "plate_number": user_info['plate_number'],
            "enrolled_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_fingerprint_database(database)
        
        print(f"🎉 Successfully enrolled {user_info['full_name']} ({user_info['user_type']}) at slot #{location}")
        
        # Create success message based on user type
        if user_info['user_type'] == 'STUDENT':
            success_message = f"""
Enrollment Successful! ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Student: {user_info['full_name']}
🆔 Student No.: {user_info['student_id']}
📚 Course: {user_info['course']}
🪪 License: {user_info['license_number']}
🏍️ Plate: {user_info['plate_number']}
🔒 Fingerprint Slot: #{location}
📅 Enrolled: {time.strftime("%Y-%m-%d %H:%M:%S")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        else:  # STAFF
            success_message = f"""
Enrollment Successful! ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Staff: {user_info['full_name']}
🆔 Staff No.: {user_info['staff_no']}
👔 Role: {user_info['staff_role']}
🪪 License: {user_info['license_number']}
🏍️ Plate: {user_info['plate_number']}
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
    """Authenticate fingerprint and return user info with retry mechanism - Updated for Students & Staff"""
    import tkinter as tk
    from tkinter import messagebox
    
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
                
                # FIXED: Use GUI button instead of console input
                try_again = messagebox.askyesno(
                    "Fingerprint Not Found",
                    f"No fingerprint match found.\n\nAttempt {attempts}/{max_attempts}\n\nWould you like to try again?",
                    icon='warning'
                )
                
                if not try_again:
                    print("❌ Authentication cancelled by user")
                    return None
                continue
            else:
                print("❌ Maximum attempts reached. No match found.")
                return None
        
        # Authentication successful - get user info
        database = load_fingerprint_database()
        finger_id = str(finger.finger_id)
        
        if finger_id in database:
            user_info = database[finger_id]
            user_type = user_info.get('user_type', 'STUDENT')
            
            print(f"✅ Authentication successful!")
            print(f"👤 Welcome: {user_info['name']} ({user_type})")
            
            if user_type == 'STUDENT':
                print(f"🆔 Student ID: {user_info.get('student_id', 'N/A')}")
                print(f"📚 Course: {user_info.get('course', 'N/A')}")
            else:  # STAFF
                print(f"🆔 Staff No.: {user_info.get('staff_no', 'N/A')}")
                print(f"👔 Role: {user_info.get('staff_role', 'N/A')}")
            
            print(f"🎯 Confidence: {finger.confidence}")
            
            # Return standardized user info for time tracking
            return {
                "name": user_info['name'],
                "student_id": user_info.get('unified_id', user_info.get('student_id', user_info.get('staff_no', 'N/A'))),
                "unified_id": user_info.get('unified_id', user_info.get('student_id', user_info.get('staff_no', 'N/A'))),
                "user_type": user_type,
                "course": user_info.get('course', user_info.get('staff_role', 'N/A')),
                "license_number": user_info.get('license_number', 'N/A'),
                "license_expiration": user_info.get('license_expiration', 'N/A'),
                "plate_number": user_info.get('plate_number', 'N/A'),
                "finger_id": finger.finger_id,
                "confidence": finger.confidence,
                "enrolled_date": user_info.get('enrolled_date', 'Unknown')
            }
        else:
            print(f"⚠️ Fingerprint recognized (ID: {finger.finger_id}) but no user data found")
            return {
                "name": f"Unknown User (ID: {finger.finger_id})",
                "student_id": "N/A",
                "unified_id": "N/A",
                "user_type": "UNKNOWN",
                "course": "N/A",
                "license_number": "N/A",
                "license_expiration": "N/A",
                "plate_number": "N/A",
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
    return enroll_finger_with_user_info(location)
