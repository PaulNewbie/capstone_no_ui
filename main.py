# main.py - MotorPass GUI Application with proper cleanup
import os
import sqlite3
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

def initialize_system():
    """Initialize system components"""
    print(f"🚗 {SYSTEM_NAME} System Initialization")
    print("="*50)
    
    # Initialize LED system
    led_ok = init_led_system(red_pin=18, green_pin=16)
    print(f"💡 LED System: {'✅' if led_ok else '❌'}")
    
    # Initialize camera once at startup
    try:
        from services.startup_init import initialize_camera_at_startup
        camera_ok = initialize_camera_at_startup()
        print(f"📷 Camera System: {'✅' if camera_ok else '❌'}")
    except Exception as e:
        print(f"📷 Camera System: ❌ ({e})")
    
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
        
        # Only cleanup OpenCV windows, not camera
        from services.rpi_camera import force_camera_cleanup
        force_camera_cleanup()
        
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

if __name__ == "__main__":
    print(f"🚗 {SYSTEM_NAME} v{SYSTEM_VERSION}")
    print("="*50)
    
    # Initialize system components
    if initialize_system():
        print("🖥️ Starting GUI interface...")
        
        try:
            # Create and run GUI using the separate UI class
            app = MotorPassGUI(
                system_name=SYSTEM_NAME,
                system_version=SYSTEM_VERSION,
                admin_function=admin_panel,
                student_function=student_verification,
                guest_function=guest_verification
            )
            app.run()
            
        except KeyboardInterrupt:
            print("\n\n⚠️ System interrupted by user")
        except Exception as e:
            print(f"❌ GUI Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cleanup_system()
    else:
        print("❌ Cannot start - check system configuration")
        input("Press Enter to exit...")
