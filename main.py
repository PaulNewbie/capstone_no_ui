## main.py - MotorPass System with Admin/Student/Guest Separation + Integrated Time In/Out System
from config import *
from controllers.admin import admin_panel
from controllers.student import student_verification
from controllers.guest import guest_verification

from utils.display_helpers import display_menu, get_user_input, display_separator, get_num

from services.fingerprint import *
from services.license_reader import *
from services.helmet_infer import *
from time_tracker import *

# =================== MAIN SYSTEM FUNCTIONS ===================


def initialize_system():
    """Initialize and test system components"""
    print(f"🚗 {SYSTEM_NAME} System Initialization")
    display_separator()
    
    try:
        # Test fingerprint sensor
        print("🔒 Testing fingerprint sensor...")
        if finger.verify_password() != adafruit_fingerprint.OK:
            print("❌ Fingerprint sensor not found!")
            return False
        
        if finger.read_templates() == adafruit_fingerprint.OK:
            print(f"✅ Sensor connected! {finger.template_count}/{finger.library_size} enrolled")
        
        # Initialize time tracking database
        print("🕒 Initializing time tracking system...")
        if init_time_database():
            print("✅ Time tracking database ready!")
        else:
            print("⚠️ Time tracking database initialization failed")
        
        # Test student database
        try:
            import sqlite3
            conn = sqlite3.connect("students.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM students")
            student_count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ Database connected! {student_count} students available")
        except:
            print("⚠️ Student database not found - use admin sync to populate")
        
        # Test webcam
        test_webcam = IPWebcam(WEBCAM_URL)
        test_frame = test_webcam.get_frame()
        
        if test_frame is not None:
            print("✅ IP webcam connected!")
        else:
            print("⚠️ IP webcam connection failed - check network and app")
        
        display_separator()
        print("✅ System initialization complete!")
        return True
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False

def main_system():
    """Main system controller"""
    print(f"🚗 Welcome to {SYSTEM_NAME}!")
    
    while True:
        display_menu(MAIN_MENU)
        choice = get_user_input("Select user type")
        
        actions = {
            "1": ("🔍 Entering Admin Panel...", admin_panel),
            "2": ("🎓 Starting Student Verification & Time Tracking...", student_verification),
            "3": ("👤 Starting Guest Verification...", guest_verification)
        }
        
        if choice in actions:
            message, action = actions[choice]
            print(message)
            action()
        elif choice == "4":
            print("👋 Thank you for using MotorPass! Drive safely!")
            break
        else:
            print("❌ Invalid option. Please try again.")

# =================== MAIN EXECUTION ===================

if __name__ == "__main__":
    print(f"🚗 {SYSTEM_NAME} - Fingerprint & License Verification System")
    print(f"🔧 Version {SYSTEM_VERSION} - Admin/Student/Guest with Integrated Time Tracking")
    display_separator()
    
    if initialize_system():
        main_system()
    else:
        print("❌ Cannot start system due to initialization errors.")
        print("🔧 Please check your hardware connections and try again.")
