# controllers/student.py - Fixed with proper camera cleanup

from services.fingerprint import authenticate_fingerprint
from services.license_reader import *
from services.helmet_infer import verify_helmet
from services.led_control import *
from services.buzzer_control import *
from services.rpi_camera import force_camera_cleanup

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
import tkinter as tk

def student_verification():
    """Main student/staff verification with GUI"""
    print("\n🎓👔 STUDENT/STAFF VERIFICATION")
    print("🖥️ Opening GUI interface...")
    
    # Import GUI here to avoid circular imports
    from ui.student_gui import StudentVerificationGUI
    
    # Force cleanup before starting
    force_camera_cleanup()
    
    # Create and run GUI
    gui = StudentVerificationGUI(run_verification_with_gui)
    gui.run()
    
    # Final cleanup after GUI closes
    force_camera_cleanup()
    
def run_verification_with_gui(status_callback):
    """Run verification steps with GUI status updates"""
    
    # Initialize systems
    init_buzzer()
    set_led_processing()
    play_processing()
    
    try:
        # Step 1: Helmet verification
        status_callback({'current_step': '🪖 Checking helmet... (Check terminal for camera)'})
        status_callback({'helmet_status': 'CHECKING'})
        
        print("\n" + "="*60)
        print("🪖 HELMET VERIFICATION (Terminal Camera)")
        print("="*60)
        
        # Ensure camera is clean before helmet check
        force_camera_cleanup()
        
        if verify_helmet():
            status_callback({'helmet_status': 'VERIFIED'})
            status_callback({'current_step': '✅ Helmet verified successfully!'})
            print("✅ Helmet verification successful")
        else:
            status_callback({'helmet_status': 'FAILED'})
            status_callback({'current_step': '❌ Helmet verification failed'})
            set_led_idle()
            play_failure()
            cleanup_buzzer()
            force_camera_cleanup()
            return {'verified': False, 'reason': 'Helmet verification failed'}
        
        # Ensure camera is cleaned up after helmet check
        force_camera_cleanup()
        time.sleep(0.5)  # Brief pause to ensure cleanup
        
        # Step 2: Fingerprint authentication
        status_callback({'current_step': '🔒 Place your finger on the sensor...'})
        status_callback({'fingerprint_status': 'PROCESSING'})
        
        print("\n" + "="*60)
        print("🔒 FINGERPRINT AUTHENTICATION")
        print("="*60)
        
        user_info = authenticate_fingerprint()
        
        if not user_info:
            status_callback({'fingerprint_status': 'FAILED'})
            status_callback({'current_step': '❌ Fingerprint authentication failed'})
            set_led_idle()
            play_failure()
            cleanup_buzzer()
            return {'verified': False, 'reason': 'Fingerprint authentication failed'}
        
        status_callback({'fingerprint_status': 'VERIFIED'})
        status_callback({'user_info': user_info})
        status_callback({'current_step': f'✅ Authenticated: {user_info["name"]}'})
        
        # Step 3: Check time status
        current_status = get_student_time_status(user_info['unified_id'])
        
        # Step 4: License verification (only for TIME IN)
        if current_status == 'OUT' or current_status is None:
            # Check license expiration
            license_expiration_valid = check_license_expiration(user_info)
            
            if not license_expiration_valid:
                status_callback({'license_status': 'EXPIRED'})
                status_callback({'current_step': '❌ License has expired'})
                set_led_idle()
                play_failure()
                cleanup_buzzer()
                return {'verified': False, 'reason': 'License has expired'}
            
            status_callback({'license_status': 'VALID'})
            
            # License capture and verification
            status_callback({'current_step': '📄 Capturing license... (Check terminal for camera)'})
            
            print("\n" + "="*60)
            print("📄 LICENSE CAPTURE (Terminal Camera)")
            print("="*60)
            
            # Force cleanup before license capture
            force_camera_cleanup()
            time.sleep(0.5)  # Brief pause
            
            image_path = auto_capture_license_rpi(
                reference_name=user_info['name'],
                fingerprint_info=user_info
            )
            
            if not image_path:
                status_callback({'current_step': '❌ License capture failed'})
                set_led_idle()
                play_failure()
                cleanup_buzzer()
                force_camera_cleanup()
                return {'verified': False, 'reason': 'License capture failed'}
            
            # Verify license
            is_fully_verified = complete_verification_flow(
                image_path=image_path,
                fingerprint_info=user_info,
                helmet_verified=True,
                license_expiration_valid=license_expiration_valid
            )
            
            # Show verification summary
            verification_summary = {
                'helmet': True,
                'fingerprint': True,
                'license_valid': license_expiration_valid,
                'license_detected': "Driver's License Detected" in str(is_fully_verified),
                'name_match': is_fully_verified
            }
            status_callback({'verification_summary': verification_summary})
            
            if is_fully_verified:
                # Record TIME IN
                if record_time_in(user_info):
                    timestamp = time.strftime('%H:%M:%S')
                    status_callback({'current_step': f'✅ TIME IN recorded at {timestamp}'})
                    set_led_success(duration=5.0)
                    play_success()
                    
                    result = {
                        'verified': True,
                        'name': user_info['name'],
                        'time_action': 'IN',
                        'timestamp': timestamp
                    }
                else:
                    status_callback({'current_step': '❌ Failed to record TIME IN'})
                    set_led_idle()
                    play_failure()
                    result = {'verified': False, 'reason': 'Failed to record TIME IN'}
            else:
                status_callback({'current_step': '❌ Verification incomplete'})
                set_led_idle()
                play_failure()
                result = {'verified': False, 'reason': 'Verification requirements not met'}
                
        else:
            # TIME OUT - simpler process
            status_callback({'license_status': 'VALID'})
            status_callback({'current_step': '🔴 Processing TIME OUT...'})
            
            # Show verification summary for TIME OUT
            verification_summary = {
                'helmet': True,
                'fingerprint': True,
                'license_valid': True,
                'license_detected': True,
                'name_match': True
            }
            status_callback({'verification_summary': verification_summary})
            
            if record_time_out(user_info):
                timestamp = time.strftime('%H:%M:%S')
                status_callback({'current_step': f'✅ TIME OUT recorded at {timestamp}'})
                set_led_success(duration=5.0)
                play_success()
                
                result = {
                    'verified': True,
                    'name': user_info['name'],
                    'time_action': 'OUT',
                    'timestamp': timestamp
                }
            else:
                status_callback({'current_step': '❌ Failed to record TIME OUT'})
                set_led_idle()
                play_failure()
                result = {'verified': False, 'reason': 'Failed to record TIME OUT'}
        
        cleanup_buzzer()
        force_camera_cleanup()
        return result
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        set_led_idle()
        play_failure()
        cleanup_buzzer()
        force_camera_cleanup()
        return {'verified': False, 'reason': str(e)}

def check_license_expiration(student_info):
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
