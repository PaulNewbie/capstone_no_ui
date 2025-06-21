# controllers/student.py - Cleaned and Optimized

from services.fingerprint import authenticate_fingerprint
from services.license_reader import auto_capture_license_rpi, complete_verification_flow
from services.helmet_infer import verify_helmet
from services.led_control import *

# Import database operations
from dashboard.database.db_operations import (
    get_student_time_status,
    record_time_in,
    record_time_out
)

import time
from datetime import datetime

def student_verification():
    """Main student verification workflow with integrated time tracking"""
    print("\n🎓 STUDENT VERIFICATION & TIME TRACKING SYSTEM")
    
    set_led_processing()
    
    # Step 1: Helmet verification
    print("🪖 Checking helmet...")
    if not verify_helmet():
        print("❌ Helmet verification failed")
        set_led_idle()
        input("\n📱 Press Enter to return to main menu...")
        return
    
    print("✅ Helmet verified")
    
    # Step 2: Fingerprint authentication
    print("🔒 Place your finger on the sensor...")
    student_info = authenticate_fingerprint()
    
    if not student_info:
        print("❌ Authentication failed")
        set_led_idle()
        input("\n📱 Press Enter to return to main menu...")
        return
    
    print(f"✅ {student_info['name']} (ID: {student_info['student_id']})")
    
    # Step 3: Check current time status
    current_status = get_student_time_status(student_info['student_id'])
    
    if current_status == 'OUT' or current_status is None:
        # Student is timing IN - full verification required
        _process_student_time_in(student_info)
    else:
        # Student is timing OUT - simplified process
        _process_student_time_out(student_info)
    
    input("\n📱 Press Enter to return to main menu...")

def _process_student_time_in(student_info):
    """Process student time in with full verification"""
    print("🟢 TIMING IN - Starting license verification...")
    
    # Step 1: License expiration check
    license_expiration_valid = _check_license_expiration(student_info)
    if not license_expiration_valid:
        print("❌ License expired")
        set_led_idle()
        return
    
    # Step 2: Capture and verify license
    image_path = auto_capture_license_rpi(
        reference_name=student_info['name'], 
        fingerprint_info=student_info
    )
    
    if not image_path:
        print("❌ License capture failed")
        set_led_idle()
        return
    
    # Step 3: Complete verification
    is_fully_verified = complete_verification_flow(
        image_path=image_path,
        fingerprint_info=student_info,
        helmet_verified=True,
        license_expiration_valid=license_expiration_valid
    )
    
    # Step 4: Record time in if verified
    if is_fully_verified:
        if record_time_in(student_info):
            print(f"✅ TIME IN SUCCESSFUL - {time.strftime('%H:%M:%S')}")
            set_led_success(duration=5.0)
        else:
            print("❌ Failed to record TIME IN")
            set_led_idle()
    else:
        print("❌ VERIFICATION INCOMPLETE - TIME IN DENIED")
        set_led_idle()

def _process_student_time_out(student_info):
    """Process student time out - simplified"""
    print("🔴 TIMING OUT...")
    print("🛡️ Drive safe!")
    
    if record_time_out(student_info):
        print(f"✅ TIME OUT SUCCESSFUL - {time.strftime('%H:%M:%S')}")
        set_led_success(duration=5.0)
    else:
        print("❌ Failed to record TIME OUT")
        set_led_idle()

def _check_license_expiration(student_info):
    """Check if student's license is expired"""
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
