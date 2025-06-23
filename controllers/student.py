# controllers/student.py - Fixed License Expiration Issue with License Retry

from services.fingerprint import authenticate_fingerprint
from services.license_reader import auto_capture_license_rpi, complete_verification_flow
from services.helmet_infer import verify_helmet
from services.led_control import *
from services.buzzer_control import play_processing, play_success, play_failure

from database.db_operations import (
    get_student_time_status,
    record_time_in,
    record_time_out
)

import time
from datetime import datetime

# Add this new function before the existing functions
def authenticate_fingerprint_with_callback(status_callback=None):
    """Authenticate fingerprint with detailed GUI feedback"""
    if status_callback:
        status_callback("message", "🔒 Fingerprint Authentication Starting...\n👆 Place finger on sensor...")
    
    try:
        from services.fingerprint import authenticate_fingerprint
        
        # The original function already handles retries internally
        student_info = authenticate_fingerprint()
        
        if student_info and student_info.get('student_id') != 'N/A':
            return student_info
        else:
            if status_callback:
                status_callback("message", "❌ No fingerprint match found\n🚫 Authentication failed after multiple attempts")
            return None
                    
    except Exception as e:
        if status_callback:
            status_callback("message", f"❌ Fingerprint sensor error:\n🔧 {str(e)}")
        return None

def student_verification():
    """Main student verification with GUI"""
    try:
        from ui.student_gui import show_student_verification_gui
        print("🎓 Starting Student Verification GUI...")
        show_student_verification_gui()
    except ImportError as e:
        print(f"❌ GUI not available ({e}), using console mode")
        console_student_verification()
    except Exception as e:
        print(f"❌ GUI Error: {e}")
        console_student_verification()
    finally:
        cleanup_camera()

def console_student_verification():
    """Console-based verification"""
    print("\n🎓 STUDENT VERIFICATION & TIME TRACKING SYSTEM")
    
    set_led_processing()
    play_processing()
    
    # Step 1: Helmet verification
    print("🪖 Checking helmet...")
    if not verify_helmet():
        print("❌ Helmet verification failed")
        set_led_idle()
        #play_failure()
        input("\n📱 Press Enter to return to main menu...")
        return
    
    print("✅ Helmet verified")
    
    # Step 2: Fingerprint authentication
    print("🔒 Place your finger on the sensor...")
    student_info = authenticate_fingerprint()
    
    if not student_info:
        print("❌ Authentication failed")
        set_led_idle()
        #play_failure()
        input("\n📱 Press Enter to return to main menu...")
        return
    
    print(f"✅ {student_info['name']} (ID: {student_info['student_id']})")
    
    # Step 3: Check current time status
    current_status = get_student_time_status(student_info['student_id'])
    
    if current_status == 'OUT' or current_status is None:
        _process_student_time_in(student_info)
    else:
        _process_student_time_out(student_info)
    
    input("\n📱 Press Enter to return to main menu...")

def run_verification_steps(status_callback=None):
    """Run verification steps with detailed console-like feedback"""
    try:
        set_led_processing()
        play_processing()
        
        # Step 1: Helmet verification
        if status_callback:
            status_callback("helmet", "PROCESSING")
            status_callback("message", "🪖 Helmet Verification Starting...")
        
        if not verify_helmet():
            if status_callback:
                status_callback("helmet", "FAILED")
                status_callback("message", "❌ Helmet verification failed\n🪖 Please wear a full-face helmet (not nutshell type)")
            set_led_idle()
            #play_failure()
            return None
        
        if status_callback:
            status_callback("helmet", "VERIFIED")
            status_callback("message", "✅ Helmet verification successful!\n🪖 Full-face helmet detected")
        
        # Step 2: Fingerprint authentication with detailed feedback
        if status_callback:
            status_callback("fingerprint", "PROCESSING")
            status_callback("message", "🔒 Fingerprint Authentication Starting...\n👆 Place your finger on the sensor")
        
        # Use existing authenticate_fingerprint with custom feedback
        student_info = authenticate_fingerprint_with_callback(status_callback)
        
        if not student_info:
            if status_callback:
                status_callback("fingerprint", "FAILED")
                status_callback("message", "❌ Fingerprint authentication failed\n🚫 Maximum attempts reached")
            set_led_idle()
            play_failure()
            return None
        
        if status_callback:
            status_callback("fingerprint", "VERIFIED")
            
            # Send detailed student info immediately
            formatted_name = student_info['name']
            if ',' in formatted_name:
                parts = formatted_name.split(',')
                if len(parts) == 2:
                    formatted_name = f"{parts[0].strip()}, {parts[1].strip()}"
            
            student_details = f"✅ Authentication successful!\n👤 Welcome: {formatted_name}\n🆔 ID: {student_info['student_id']}\n📚 Course: {student_info.get('course', 'N/A')}\n🎯 Confidence: {student_info.get('confidence', 0)}"
            status_callback("message", student_details)
            
            # Send student info for display panel
            status_callback("student_info", {
                'name': student_info['name'],
                'student_id': student_info['student_id'],
                'course': student_info.get('course', 'N/A'),
                'confidence': student_info.get('confidence', 0)
            })
        
        # Step 3: Determine time action
        current_status = get_student_time_status(student_info['student_id'])
        
        if current_status == 'OUT' or current_status is None:
            return process_time_in_gui(student_info, status_callback)
        else:
            return process_time_out_gui(student_info, status_callback)
            
    except Exception as e:
        if status_callback:
            status_callback("message", f"❌ System Error: {str(e)}")
        set_led_idle()
        play_failure()
        return None

def process_time_in_gui(student_info, status_callback=None):
    """Process TIME IN for GUI with license retry functionality"""
    try:
        # Check license expiration (lenient check)
        if status_callback:
            status_callback("license", "PROCESSING")
            status_callback("message", "📅 License Validation Starting...\n🔍 Checking license expiration date")
        
        license_valid, warning_msg = _check_license_expiration_lenient(student_info)
        
        if warning_msg:
            print(f"⚠️ License Warning: {warning_msg}")
            if status_callback:
                status_callback("message", f"⚠️ License Warning Detected:\n{warning_msg}\n🔄 Proceeding with verification...")
        
        # Continue even if license check has warnings (but not if completely invalid)
        if not license_valid and "expired" in warning_msg.lower():
            if status_callback:
                status_callback("license", "FAILED")
                status_callback("message", "❌ License Expired - Access Denied\n📅 Please renew your license before entry")
            set_led_idle()
            play_failure()
            return None
        
        # License verification with retry logic
        max_license_retries = 3
        license_retry_count = 0
        
        while license_retry_count < max_license_retries:
            try:
                if license_retry_count > 0:
                    if status_callback:
                        status_callback("message", f"🔄 License Retry Attempt {license_retry_count + 1}/{max_license_retries}\n📷 Please position your license clearly")
                else:
                    if status_callback:
                        status_callback("message", "📄 License Document Verification\n📷 Please show your license to the camera")
                
                # Capture license image
                image_path = auto_capture_license_rpi(
                    reference_name=student_info['name'], 
                    fingerprint_info=student_info
                )
                
                if not image_path:
                    license_retry_count += 1
                    if license_retry_count < max_license_retries:
                        if status_callback:
                            status_callback("message", f"❌ License Capture Failed - Attempt {license_retry_count}/{max_license_retries}\n🔄 Preparing to retry...")
                        time.sleep(2)  # Brief pause before retry
                        continue
                    else:
                        if status_callback:
                            status_callback("license", "FAILED")
                            status_callback("message", "❌ License Capture Failed - Maximum Retries Reached\n📷 Could not capture license image")
                        set_led_idle()
                        play_failure()
                        return None
                
                if status_callback:
                    status_callback("message", "🔍 Analyzing License Document...\n📋 Verifying authenticity and details")
                
                # Verify the license
                is_verified = complete_verification_flow(
                    image_path=image_path,
                    fingerprint_info=student_info,
                    helmet_verified=True,
                    license_expiration_valid=license_valid
                )
                
                if is_verified:
                    # Success - break out of retry loop
                    if status_callback:
                        status_callback("license", "VALID")
                        status_callback("message", "✅ License Verification Complete!\n⏳ Recording TIME IN to system...")
                        # Show verification summary for success case
                        status_callback("verification_summary", {
                            'helmet': True,
                            'fingerprint': True,
                            'license_valid': license_valid,
                            'license_detected': True,
                            'name_match': True
                        })
                    break
                else:
                    # License verification failed
                    license_retry_count += 1
                    
                    if license_retry_count < max_license_retries:
                        # Ask user if they want to retry
                        if status_callback:
                            retry_msg = f"❌ License Verification Failed - Attempt {license_retry_count}/{max_license_retries}\n\n"
                            retry_msg += "Possible issues:\n"
                            retry_msg += "• License not clearly visible\n"
                            retry_msg += "• Poor lighting conditions\n"
                            retry_msg += "• Document not fully in frame\n\n"
                            retry_msg += f"🔄 Retrying automatically in 3 seconds... ({max_license_retries - license_retry_count} attempts remaining)"
                            status_callback("message", retry_msg)
                        
                        time.sleep(3)  # Give user time to read the message
                        continue
                    else:
                        # Maximum retries reached
                        if status_callback:
                            status_callback("license", "FAILED")
                            status_callback("message", "❌ License Verification Failed - Maximum Retries Reached\n📄 Document could not be validated after multiple attempts")
                            # Show verification summary for failed case
                            status_callback("verification_summary", {
                                'helmet': True,
                                'fingerprint': True,
                                'license_valid': license_valid,
                                'license_detected': False,
                                'name_match': False
                            })
                        set_led_idle()
                        play_failure()
                        return None
                        
            except Exception as e:
                license_retry_count += 1
                if license_retry_count < max_license_retries:
                    if status_callback:
                        status_callback("message", f"❌ License Processing Error - Attempt {license_retry_count}/{max_license_retries}\n🔧 {str(e)}\n🔄 Retrying...")
                    time.sleep(2)
                    continue
                else:
                    if status_callback:
                        status_callback("license", "FAILED")
                        status_callback("message", f"❌ License Processing Error - Maximum Retries Reached\n🔧 {str(e)}")
                    set_led_idle()
                    play_failure()
                    return None
        
        # Record time in (only reached if license verification succeeded)
        if record_time_in(student_info):
            set_led_success(duration=5.0)
            play_success()
            
            if status_callback:
                status_callback("message", "✅ TIME IN Successful!\n🎉 Welcome to campus! Have a great day!")
            
            return {
                'name': student_info['name'],
                'student_id': student_info['student_id'],
                'course': student_info.get('course', 'N/A'),
                'license_number': student_info.get('license_number', 'N/A'),
                'time_action': 'IN',
                'timestamp': time.strftime('%H:%M:%S'),
                'verified': True
            }
        else:
            if status_callback:
                status_callback("message", "❌ Database Error\n💾 Failed to record TIME IN")
            set_led_idle()
            play_failure()
            return None
            
    except Exception as e:
        if status_callback:
            status_callback("license", "FAILED")
            status_callback("message", f"❌ TIME IN Processing Error:\n🔧 {str(e)}")
        set_led_idle()
        play_failure()
        return None

def process_time_out_gui(student_info, status_callback=None):
    """Process TIME OUT for GUI with detailed feedback"""
    try:
        if status_callback:
            status_callback("license", "VALID")  # Skip license check for time out
            status_callback("message", "🔴 TIME OUT Process Starting...\n⏳ Recording exit from campus")
        
        if record_time_out(student_info):
            set_led_success(duration=5.0)
            play_success()
            
            if status_callback:
                status_callback("message", "✅ TIME OUT Successful!\n🛡️ Drive safely! Your exit has been logged.")
            
            return {
                'name': student_info['name'],
                'student_id': student_info['student_id'],
                'course': student_info.get('course', 'N/A'),
                'license_number': student_info.get('license_number', 'N/A'),
                'time_action': 'OUT',
                'timestamp': time.strftime('%H:%M:%S'),
                'verified': True
            }
        else:
            if status_callback:
                status_callback("message", "❌ Database Error\n💾 Failed to record TIME OUT")
            set_led_idle()
            #play_failure()
            return None
            
    except Exception as e:
        if status_callback:
            status_callback("message", f"❌ TIME OUT Processing Error:\n🔧 {str(e)}")
        set_led_idle()
        play_failure()
        return None

def _check_license_expiration_lenient(student_info):
    """Lenient license expiration check that allows missing data"""
    try:
        expiration_date_str = student_info.get('license_expiration', '')
        
        # Handle missing or placeholder data
        if not expiration_date_str or expiration_date_str in ['N/A', 'None', '', 'Unknown']:
            return True, "License expiration date not available"
        
        # Try to parse the date in multiple formats
        expiration_date = None
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
        
        for date_format in date_formats:
            try:
                expiration_date = datetime.strptime(expiration_date_str.strip(), date_format)
                break
            except ValueError:
                continue
        
        if not expiration_date:
            return True, f"License date format not recognized: {expiration_date_str}"
        
        current_date = datetime.now()
        
        if expiration_date.date() < current_date.date():
            days_expired = (current_date.date() - expiration_date.date()).days
            return False, f"License expired {days_expired} days ago"
        else:
            days_until_expiry = (expiration_date.date() - current_date.date()).days
            if days_until_expiry <= 30:
                return True, f"License expires in {days_until_expiry} days"
            else:
                return True, ""
            
    except Exception as e:
        print(f"❌ Error checking license: {e}")
        return True, f"License check error: {str(e)}"

# Keep the original functions for console mode
def _process_student_time_in(student_info):
    """Process student time in with full verification"""
    print("🟢 TIMING IN - Starting license verification...")
    
    license_valid, warning_msg = _check_license_expiration_lenient(student_info)
    if warning_msg:
        print(f"⚠️ {warning_msg}")
    
    if not license_valid and "expired" in warning_msg.lower():
        print("❌ License expired - Cannot proceed")
        set_led_idle()
        #play_failure()
        return
    
    image_path = auto_capture_license_rpi(
        reference_name=student_info['name'], 
        fingerprint_info=student_info
    )
    
    if not image_path:
        print("❌ License capture failed")
        set_led_idle()
        #play_failure()
        return
    
    is_fully_verified = complete_verification_flow(
        image_path=image_path,
        fingerprint_info=student_info,
        helmet_verified=True,
        license_expiration_valid=license_valid
    )
    
    if is_fully_verified:
        if record_time_in(student_info):
            print(f"✅ TIME IN SUCCESSFUL - {time.strftime('%H:%M:%S')}")
            print("🎉 Welcome to campus! Have a great day!")
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

def _process_student_time_out(student_info):
    """Process student time out - simplified"""
    print("🔴 TIMING OUT...")
    print("🛡️ Drive safe!")
    
    if record_time_out(student_info):
        print(f"✅ TIME OUT SUCCESSFUL - {time.strftime('%H:%M:%S')}")
        set_led_success(duration=5.0)
        play_success()
    else:
        print("❌ Failed to record TIME OUT")
        set_led_idle()
        play_failure()
        
def cleanup_camera():
    """Simple camera cleanup"""
    try:
        import cv2
        cv2.destroyAllWindows()
        
        # Release any camera that might be in use
        for i in range(3):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    cap.release()
            except:
                pass
    except:
        pass
