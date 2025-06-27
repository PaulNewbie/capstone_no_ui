# controllers/student.py - Fixed with proper license expiration handling

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
    
    # No cleanup needed here - will be handled by verification process
    
    # Create and run GUI
    gui = StudentVerificationGUI(run_verification_with_gui)
    gui.run()
    
    # No cleanup needed here - camera is already cleaned up

def run_verification_with_gui(status_callback):
    """Run verification steps with GUI status updates - Smart cleanup"""
    
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
        
        # No cleanup needed - helmet verification handles it internally
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
            # No camera cleanup needed - helmet verification already cleaned up
            return {'verified': False, 'reason': 'Helmet verification failed'}
        
        # Step 2: Fingerprint verification
        status_callback({'current_step': '👆 Please place your finger on the scanner'})
        status_callback({'fingerprint_status': 'WAITING'})
        
        user_info = authenticate_fingerprint()
        
        if not user_info:
            status_callback({'fingerprint_status': 'FAILED'})
            status_callback({'current_step': '❌ Fingerprint authentication failed'})
            set_led_idle()
            play_failure()
            cleanup_buzzer()
            return {'verified': False, 'reason': 'Fingerprint authentication failed'}
        
        status_callback({'fingerprint_status': 'VERIFIED'})
        status_callback({'student_info': user_info})
        
        # Step 2.5: Process license expiration data
        license_expiration_valid = False
        days_left = 0
        
        # Check if days_until_expiration is already in user_info
        if 'days_until_expiration' in user_info:
            days_left = user_info['days_until_expiration']
            license_expiration_valid = days_left > 0
        else:
            # Try to calculate from license_expiration field
            if 'license_expiration' in user_info:
                license_expiration_valid = check_license_expiration(user_info)
                if license_expiration_valid:
                    # Calculate days_left for display purposes
                    expiration_date_str = user_info.get('license_expiration', '')
                    try:
                        # Parse the expiration date (multiple formats)
                        try:
                            expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d')
                        except ValueError:
                            try:
                                expiration_date = datetime.strptime(expiration_date_str, '%m/%d/%Y')
                            except ValueError:
                                expiration_date = datetime.strptime(expiration_date_str, '%d/%m/%Y')
                        
                        current_date = datetime.now()
                        days_left = (expiration_date.date() - current_date.date()).days
                        
                        # Add calculated days to user_info for consistency
                        user_info['days_until_expiration'] = days_left
                        
                    except Exception as e:
                        print(f"❌ Error calculating days until expiration: {e}")
                        days_left = 0
                else:
                    days_left = 0
            else:
                # No license expiration information available at all
                print("⚠️ Warning: No license expiration information found")
                print("📝 Available user_info keys:", list(user_info.keys()))
                
                # For debugging - show what fields are available
                status_callback({'current_step': '⚠️ Warning: No license expiration data found, proceeding with verification...'})
                
                # Set as valid to continue with verification (you may want to change this behavior)
                license_expiration_valid = True
                days_left = 999  # Placeholder value
                
                # Alternative: Fail the verification if no expiration data
                # status_callback({'license_status': 'FAILED'})
                # status_callback({'current_step': '❌ No license expiration information available'})
                # set_led_idle()
                # play_failure()
                # cleanup_buzzer()
                # return {'verified': False, 'reason': 'No license expiration information available'}
        
        # Check if license is expired
        if days_left <= 0 and 'license_expiration' in user_info:
            status_callback({'license_status': 'EXPIRED'})
            status_callback({
                'current_step': f'❌ License expired {abs(days_left)} days ago!'
            })
            set_led_idle()
            play_failure()
            cleanup_buzzer()
            return {'verified': False, 'reason': 'License has expired'}
        
        # License is valid or no expiration data available
        status_callback({'license_status': 'VALID'})
        
        # Step 3: License capture and verification
        status_callback({'current_step': '📄 Capturing license... (Check terminal for camera)'})
        
        print("\n" + "="*60)
        print("📄 LICENSE CAPTURE (Terminal Camera)")
        print("="*60)
        
        # No cleanup before license capture - camera state is managed internally
        image_path = auto_capture_license_rpi(
            reference_name=user_info['name'],
            fingerprint_info=user_info
        )
        
        if not image_path:
            status_callback({'current_step': '❌ License capture failed'})
            set_led_idle()
            play_failure()
            cleanup_buzzer()
            # No camera cleanup needed
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
            # Record TIME IN/OUT
            current_status = get_student_time_status(user_info)
            
            if current_status == 'IN':
                # Process TIME OUT
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
                # Process TIME IN
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
        
        cleanup_buzzer()
        return result
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        set_led_idle()
        play_failure()
        cleanup_buzzer()
        return {'verified': False, 'reason': str(e)}
        
def check_license_expiration(student_info):
    """Check if student's license is expired"""
    try:
        expiration_date_str = student_info.get('license_expiration', '')
        
        if not expiration_date_str or expiration_date_str == 'N/A':
            print("⚠️ No license expiration date found")
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
