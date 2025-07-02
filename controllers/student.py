# controllers/student.py - FIXED key name for GUI callback

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
    
    # Create and run GUI
    gui = StudentVerificationGUI(run_verification_with_gui)
    gui.run()

def run_verification_with_gui(status_callback):
    """Run verification steps with GUI status updates - FIXED key name"""
    
    # Initialize systems
    init_buzzer()
    set_led_processing()
    play_processing()
    
    # Initialize result variable
    result = {'verified': False, 'reason': 'Unknown error'}
    
    try:
        # Step 1: Helmet verification
        status_callback({'current_step': '🪖 Checking helmet... (Check terminal for camera)'})
        status_callback({'helmet_status': 'CHECKING'})
        
        print("\n" + "="*60)
        print("🪖 HELMET VERIFICATION (Terminal Camera)")
        print("="*60)
        
        if not verify_helmet():
            status_callback({'helmet_status': 'FAILED'})
            status_callback({'current_step': '❌ Helmet verification failed'})
            set_led_idle()
            play_failure()
            cleanup_buzzer()
            return {'verified': False, 'reason': 'Helmet verification failed'}
        
        status_callback({'helmet_status': 'VERIFIED'})
        status_callback({'current_step': '✅ Helmet verified successfully!'})
        print("✅ Helmet verification successful")
        
        # Step 2: Fingerprint verification
        status_callback({'current_step': '👆 Please place your finger on the scanner'})
        status_callback({'fingerprint_status': 'PROCESSING'})  # Changed from WAITING to PROCESSING
        
        user_info = authenticate_fingerprint()
        
        if not user_info:
            status_callback({'fingerprint_status': 'FAILED'})
            status_callback({'current_step': '❌ Fingerprint authentication failed'})
            set_led_idle()
            play_failure()
            cleanup_buzzer()
            return {'verified': False, 'reason': 'Fingerprint authentication failed'}
        
        status_callback({'fingerprint_status': 'VERIFIED'})
        # FIXED: Change 'student_info' to 'user_info' to match GUI expectation
        status_callback({'user_info': user_info})
        
        # FIXED: Check current status with correct user_id
        user_id = user_info.get('unified_id', user_info.get('student_id', ''))
        current_status = get_student_time_status(user_id)
        
        print(f"🔍 Current status for {user_info['name']}: {current_status}")
        
        # Simple logic: Skip license scan if timing out
        if current_status == 'IN':
            # TIME OUT - Skip license scanning
            status_callback({'current_step': '🚪 Processing TIME OUT - No license scan needed'})
            
            # Show simplified verification summary
            verification_summary = {
                'helmet': True,
                'fingerprint': True,
                'license_valid': True,  # Skip for TIME OUT
                'license_detected': True,  # Skip for TIME OUT
                'name_match': True  # Already verified by fingerprint
            }
            status_callback({'verification_summary': verification_summary})
            
            # Record TIME OUT directly
            if record_time_out(user_info):
                timestamp = time.strftime('%H:%M:%S')
                status_callback({'current_step': f'✅ TIME OUT recorded at {timestamp}'})
                set_led_success(duration=5.0)
                play_success()
                
                result = {
                    'verified': True,
                    'name': user_info['name'],
                    'time_action': 'OUT',
                    'timestamp': timestamp,
                    'student_id': user_info.get('student_id', 'N/A')
                }
            else:
                status_callback({'current_step': '❌ Failed to record TIME OUT'})
                set_led_idle()
                play_failure()
                result = {'verified': False, 'reason': 'Failed to record TIME OUT'}
                
        else:
            # TIME IN - Do full verification with license scan
            status_callback({'current_step': '📄 Processing TIME IN - License scan required'})
            
            # Step 2.5: Process license expiration data
            license_expiration_valid = False
            days_left = 0
            
            if 'days_until_expiration' in user_info:
                days_left = user_info['days_until_expiration']
                license_expiration_valid = days_left > 0
            else:
                if 'license_expiration' in user_info:
                    license_expiration_valid = check_license_expiration(user_info)
                    if license_expiration_valid:
                        expiration_date_str = user_info.get('license_expiration', '')
                        try:
                            try:
                                expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d')
                            except ValueError:
                                try:
                                    expiration_date = datetime.strptime(expiration_date_str, '%m/%d/%Y')
                                except ValueError:
                                    expiration_date = datetime.strptime(expiration_date_str, '%d/%m/%Y')
                            
                            current_date = datetime.now()
                            days_left = (expiration_date.date() - current_date.date()).days
                            user_info['days_until_expiration'] = days_left
                            
                        except Exception as e:
                            print(f"❌ Error calculating days until expiration: {e}")
                            days_left = 0
                            license_expiration_valid = False
                    else:
                        days_left = 0
                else:
                    license_expiration_valid = True
                    print("ℹ️ No license expiration data found, assuming valid")
            
            # Update GUI with license expiration info
            status_callback({
                'license_expiration': {
                    'valid': license_expiration_valid,
                    'days_left': days_left,
                    'expiration_date': user_info.get('license_expiration', 'N/A')
                }
            })
            
            # Check if license has expired
            if not license_expiration_valid:
                status_callback({
                    'license_status': 'EXPIRED',
                    'current_step': f'❌ License expired ({days_left} days overdue)'
                })
                set_led_idle()
                play_failure()
                cleanup_buzzer()
                return {'verified': False, 'reason': 'License has expired'}
            
            # License is valid
            status_callback({'license_status': 'VALID'})
            
            # Step 3: License capture and verification
            status_callback({'current_step': '📄 Capturing license... (Check terminal for camera)'})
            
            print("\n" + "="*60)
            print("📄 LICENSE CAPTURE (Terminal Camera)")
            print("="*60)
            
            image_path = auto_capture_license_rpi(
                reference_name=user_info['name'],
                fingerprint_info=user_info
            )
            
            if not image_path:
                status_callback({'current_step': '❌ License capture failed'})
                set_led_idle()
                play_failure()
                cleanup_buzzer()
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
                        'timestamp': timestamp,
                        'student_id': user_info.get('student_id', 'N/A')
                    }
                else:
                    status_callback({'current_step': '❌ Failed to record TIME IN'})
                    set_led_idle()
                    play_failure()
                    result = {'verified': False, 'reason': 'Failed to record TIME IN'}
            else:
                status_callback({'current_step': '❌ Verification failed'})
                set_led_idle()
                play_failure()
                result = {'verified': False, 'reason': 'License verification failed'}
                
    except Exception as e:
        print(f"❌ Error in verification: {e}")
        status_callback({'current_step': f'❌ Error: {str(e)}'})
        set_led_idle()
        play_failure()
        result = {'verified': False, 'reason': f'Error: {str(e)}'}
    
    finally:
        cleanup_buzzer()
    
    return result
    
def check_license_expiration(user_info):
    """Check if license is expired"""
    try:
        expiration_date_str = user_info.get('license_expiration', '')
        if not expiration_date_str:
            return True  # No expiration date, assume valid
        
        # Try different date formats
        try:
            expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d')
        except ValueError:
            try:
                expiration_date = datetime.strptime(expiration_date_str, '%m/%d/%Y')
            except ValueError:
                try:
                    expiration_date = datetime.strptime(expiration_date_str, '%d/%m/%Y')
                except ValueError:
                    print(f"❌ Unknown date format: {expiration_date_str}")
                    return True  # Can't parse, assume valid
        
        current_date = datetime.now()
        return expiration_date.date() >= current_date.date()
        
    except Exception as e:
        print(f"❌ Error checking license expiration: {e}")
        return True  # Error checking, assume valid
