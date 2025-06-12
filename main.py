# main.py - MotorPass System - Clean Initialization Logs

from config import *
from controllers.admin import admin_panel
from controllers.student import student_verification
from controllers.guest import guest_verification
from utils.display_helpers import display_menu, get_user_input, display_separator, get_num
from services.fingerprint import *
from services.license_reader import *
from services.helmet_infer import *
from services.led_control import init_led_system, set_led_idle, cleanup_led_system
from services.rpi_camera import get_camera, release_camera
from time_tracker import *
import atexit

# =================== MAIN SYSTEM FUNCTIONS ===================

def initialize_system():
    """Initialize and test system components with clean logging"""
    print(f"🚗 {SYSTEM_NAME} System Initialization")
    display_separator()
    
    try:
        # Initialize LED system
        print("💡 Initializing system components...")
        led_ok = init_led_system(red_pin=18, green_pin=16)
        
        # Initialize RPi Camera 3
        camera = get_camera()
        camera_ok = camera.initialized and camera.test_camera()
        
        # Test fingerprint sensor
        finger_ok = finger.verify_password() == adafruit_fingerprint.OK
        finger_count = 0
        if finger_ok:
            # Get actual enrolled count from fingerprint database
            try:
                from services.fingerprint import load_fingerprint_database
                fingerprint_db = load_fingerprint_database()
                finger_count = len(fingerprint_db)
            except:
                # Fallback to sensor template count
                if finger.read_templates() == adafruit_fingerprint.OK:
                    finger_count = finger.template_count if finger.template_count is not None else 0
        
        # Initialize databases
        time_db_ok = init_time_database()
        
        # Test student database
        student_count = 0
        try:
            import sqlite3
            conn = sqlite3.connect("database/students.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM students")
            student_count = cursor.fetchone()[0]
            conn.close()
            student_db_ok = True
        except:
            student_db_ok = False
        
        # Test helmet detection model
        try:
            helmet_model_ok = session is not None
        except:
            helmet_model_ok = False
        
        # Display results
        status_items = [
            ("LED System", "✅" if led_ok else "⚠️"),
            ("RPi Camera 3", "✅" if camera_ok else "❌"),
            ("Fingerprint Sensor", f"✅ ({finger_count}/{finger.library_size} enrolled)" if finger_ok else "❌"),
            ("Time Tracking DB", "✅" if time_db_ok else "⚠️"),
            ("Student Database", f"✅ ({student_count} students)" if student_db_ok else "⚠️ Use admin sync"),
            ("Helmet Detection", "✅" if helmet_model_ok else "⚠️")
        ]
        
        for item, status in status_items:
            print(f"{status} {item}")
        
        display_separator()
        
        # Check critical components
        if not camera_ok or not finger_ok:
            print("❌ Critical components failed!")
            return False
        
        print("✅ System ready!")
        set_led_idle()
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
            "1": ("🔍 Admin Panel", admin_panel),
            "2": ("🎓 Student Verification", student_verification),
            "3": ("👤 Guest Verification", guest_verification)
        }
        
        if choice in actions:
            message, action = actions[choice]
            print(f"{message}...")
            action()
            set_led_idle()
        elif choice == "4":
            print("👋 Thank you for using MotorPass!")
            cleanup_system()
            break
        else:
            print("❌ Invalid option. Please try again.")

def cleanup_system():
    """Cleanup all system resources"""
    cleanup_led_system()
    release_camera()

def cleanup_on_exit():
    """Cleanup function called on system exit"""
    cleanup_system()

# Register cleanup function
atexit.register(cleanup_on_exit)

# =================== MAIN EXECUTION ===================
if __name__ == "__main__":
    print(f"🚗 {SYSTEM_NAME} v{SYSTEM_VERSION}")
    display_separator()
    
    try:
        if initialize_system():
            main_system()
        else:
            print("❌ Cannot start - check hardware connections")
    except KeyboardInterrupt:
        print("\n🛑 System interrupted")
    except Exception as e:
        print(f"❌ System error: {e}")
    finally:
        cleanup_system()
