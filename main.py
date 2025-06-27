# main.py - MotorPass GUI Application with proper cleanup
import os
import sys
import sqlite3
import subprocess
import time
from ui.main_window import MotorPassGUI

# Import controllers
from controllers.admin import admin_panel
from controllers.student import student_verification
from controllers.guest import guest_verification

# Import configuration
from config import SYSTEM_NAME, SYSTEM_VERSION

# Import services
from services.led_control import (
    init_led_system, 
    set_led_idle, 
    cleanup_led_system
)
from services.rpi_camera import force_camera_cleanup
from database.db_operations import initialize_all_databases

# Global flag to track if restart is needed
RESTART_AFTER_TRANSACTION = False

def initialize_system():
    """Initialize system components"""
    print(f"🚗 {SYSTEM_NAME} System Initialization")
    print("="*50)
    
    # Smart cleanup at startup - will only clean if needed
    force_camera_cleanup()
    
    # Initialize LED system
    led_ok = init_led_system(red_pin=18, green_pin=16)
    print(f"💡 LED System: {'✅' if led_ok else '❌'}")
    
    # Initialize all databases
    db_ok = initialize_all_databases()
    
    if not db_ok:
        print("⚠️ Some databases failed to initialize, but system will continue")
    
    print("✅ System ready!")
    set_led_idle()
    return True

def cleanup_system():
    """Cleanup system resources"""
    try:
        print("\n🧹 Cleaning up system resources...")
        cleanup_led_system()
        force_camera_cleanup()
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

def restart_application():
    """Restart the entire application"""
    print("\n🔄 Restarting application for fresh camera state...")
    
    # Clean up current resources
    cleanup_system()
    
    # Small delay to ensure cleanup
    time.sleep(1)
    
    # Get the current script path
    script_path = os.path.abspath(__file__)
    python_executable = sys.executable
    
    # Start new instance
    print("🚀 Starting new instance...")
    subprocess.Popen([python_executable, script_path])
    
    # Exit current instance
    sys.exit(0)

def student_verification_wrapper():
    """Wrapper for student verification with auto-restart"""
    global RESTART_AFTER_TRANSACTION
    
    try:
        # Run original student verification
        result = student_verification()
        
        # Set restart flag
        RESTART_AFTER_TRANSACTION = True
        
        return result
        
    except Exception as e:
        print(f"❌ Student verification error: {e}")
        RESTART_AFTER_TRANSACTION = True
        raise

def guest_verification_wrapper():
    """Wrapper for guest verification with auto-restart"""
    global RESTART_AFTER_TRANSACTION
    
    try:
        # Run original guest verification
        result = guest_verification()
        
        # Set restart flag
        RESTART_AFTER_TRANSACTION = True
        
        return result
        
    except Exception as e:
        print(f"❌ Guest verification error: {e}")
        RESTART_AFTER_TRANSACTION = True
        raise

def admin_panel_wrapper():
    """Wrapper for admin panel - no restart needed"""
    return admin_panel()

def main_loop():
    """Main application loop with restart logic"""
    global RESTART_AFTER_TRANSACTION
    
    while True:
        RESTART_AFTER_TRANSACTION = False
        
        try:
            # Create and run GUI using the separate UI class
            app = MotorPassGUI(
                system_name=SYSTEM_NAME,
                system_version=SYSTEM_VERSION,
                admin_function=admin_panel_wrapper,
                student_function=student_verification_wrapper,
                guest_function=guest_verification_wrapper
            )
            
            # Run the GUI
            app.run()
            
            # Check if restart is needed
            if RESTART_AFTER_TRANSACTION:
                print("\n🔄 Transaction completed - restarting for fresh camera state...")
                restart_application()
            else:
                # Normal exit
                break
                
        except KeyboardInterrupt:
            print("\n\n⚠️ System interrupted by user")
            break
        except Exception as e:
            print(f"❌ GUI Error: {e}")
            import traceback
            traceback.print_exc()
            
            # Check if restart is needed even after error
            if RESTART_AFTER_TRANSACTION:
                print("\n🔄 Error occurred after transaction - restarting...")
                restart_application()
            else:
                break

if __name__ == "__main__":
    print(f"🚗 {SYSTEM_NAME} v{SYSTEM_VERSION}")
    print("="*50)
    
    # Initialize system components
    if initialize_system():
        print("🖥️ Starting GUI interface...")
        
        try:
            # Start main loop with restart logic
            main_loop()
            
        finally:
            cleanup_system()
    else:
        print("❌ Cannot start - check system configuration")
        input("Press Enter to exit...")
