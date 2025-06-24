# controllers/student.py - Simplified with Clean Logging + Buzzer Integration

from services.fingerprint import authenticate_fingerprint
from services.license_reader import *
from services.helmet_infer import verify_helmet
from services.led_control import *
from services.buzzer_control import *

# Import database operations
from database.db_operations import (
    get_student_time_status,
    record_time_in,
    record_time_out
)

from utils.display_helpers import display_separator, display_verification_result
from utils.gui_helpers import show_results_gui

import time
from datetime import datetime

def student_verification():
    """Main student/staff verification workflow with integrated time tracking, LED status and buzzer"""
    print("\n🎓👔 STUDENT/STAFF VERIFICATION & TIME TRACKING SYSTEM")
    
    # Initialize buzzer system
    init_buzzer()
    
    # Set LED to processing state and play processing sound when verification starts
    set_led_processing()
    play_processing()
    
    # Step 1: Helmet verification (always required)
    print("🪖 Checking helmet...")
    if not verify_helmet():
        print("❌ Helmet verification failed")
        set_led_idle()
        play_failure()
        cleanup_buzzer()
        input("\n📱 Press Enter to return to main menu...")
        return
    print("✅ Helmet verified")
    
    # Step 2: Fingerprint authentication
    print("🔒 Place your finger on the sensor...")
    user_info = authenticate_fingerprint()
    
    if not user_info:
        print("❌ Authentication failed")
        set_led_idle()
        play_failure()
        cleanup_buzzer()
        input("\n📱 Press Enter to return to main menu...")
        return
    
    user_type = user_info.get('user_type', 'STUDENT')
    user_type_display = "Student" if user_type == 'STUDENT' else "Staff"
    
    print(f"✅ {user_info['name']} ({user_type_display} - ID: {user_info['unified_id']})")
    
    # Step 3: Check current time status first
    current_status = get_student_time_status(user_info['unified_id'])
    
    # Step 4: License expiration check (only for TIME IN)
    if current_status == 'OUT' or current_status is None:
        license_expiration_valid = check_license_expiration(user_info)
        if not license_expiration_valid:
            print("❌ License expired")
            set_led_idle()
            play_failure()
            cleanup_buzzer()
            input("\n📱 Press Enter to return to main menu...")
            return
    
    if current_status == 'OUT' or current_status is None:
        # User is timing IN - full verification required
        print(f"🟢 TIMING IN - Starting license verification for {user_type_display}...")
        
        # Capture and verify license
        image_path = auto_capture_license_rpi(reference_name=user_info['name'], 
                                           fingerprint_info=user_info)
        
        if not image_path:
            print("❌ License capture failed")
            set_led_idle()
            play_failure()
            cleanup_buzzer()
            input("\n📱 Press Enter to return to main menu...")
            return
        
        is_fully_verified = complete_verification_flow(
            image_path=image_path,
            fingerprint_info=user_info,
            helmet_verified=True,
            license_expiration_valid=license_expiration_valid
        )
        
        if is_fully_verified:
            if record_time_in(user_info):
                print(f"✅ TIME IN SUCCESSFUL - {time.strftime('%H:%M:%S')}")
                set_led_success(duration=5.0)
                play_success()
            else:
                print("❌ Failed to record TIME IN")
                set_led_idle()
                play_failure()
        else:
            print("❌ VERIFICATION INCOMPLETE - TIME IN DENIED")
            set_led_idle()
            play_failure()
        
    else:
        # User is timing OUT - only helmet + fingerprint required
        print(f"🔴 TIMING OUT {user_type_display}...")
        print("🛡️ Drive safe!")
        
        if record_time_out(user_info):
            print(f"✅ TIME OUT SUCCESSFUL - {time.strftime('%H:%M:%S')}")
            set_led_success(duration=5.0)
            play_success()
        else:
            print("❌ Failed to record TIME OUT")
            set_led_idle()
            play_failure()
    
    # Clean up buzzer before returning
    cleanup_buzzer()
    input("\n📱 Press Enter to return to main menu...")
    
def check_license_expiration(student_info):
    """Check if student's license is expired - simplified logging"""
    try:
        expiration_date_str = student_info.get('license_expiration', '')
        
        if not expiration_date_str or expiration_date_str == 'N/A':
            return False
        
        # Parse the expiration date (multiple formats)
        try:
            expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d')
        except ValueError:
            try:
                expiration_date = datetime.strptime(expiration_date_str, '%m/%d/%Y')
            except ValueError:
                try:
                    expiration_date = datetime.strptime(expiration_date_str, '%d/%m/%Y')
                except ValueError:
                    print(f"❌ Invalid date format: {expiration_date_str}")
                    return False
        
        current_date = datetime.now()
        
        if expiration_date.date() < current_date.date():
            print(f"❌ License EXPIRED: {expiration_date.strftime('%Y-%m-%d')}")
            return False
        else:
            days_until_expiry = (expiration_date.date() - current_date.date()).days
            print(f"✅ License valid ({days_until_expiry} days remaining)")
            
            if days_until_expiry <= 30:
                print(f"⚠️ Warning: License expires in {days_until_expiry} days")
            
            return True
            
    except Exception as e:
        print(f"❌ Error checking license: {e}")
        return False
