# controllers/student.py - Updated for RPi Camera 3

from services.fingerprint import authenticate_fingerprint
from services.license_reader import *
from services.helmet_infer import verify_helmet
from services.time_tracker import *
from services.led_control import set_led_processing, set_led_success, set_led_idle

from utils.display_helpers import display_separator, display_verification_result
from utils.gui_helpers import show_results_gui

import time

def student_verification():
    """Main student verification workflow with integrated time tracking and LED status"""
    print("\n🎓 STUDENT VERIFICATION & TIME TRACKING SYSTEM")
    
    # Set LED to processing state when student verification starts
    set_led_processing()
    
    # Step 1: Helmet verification (always required)
    if not verify_helmet_check():
        print("❌ Helmet verification failed - returning to idle state")
        set_led_idle()  # Return to idle on failure
        input("\n📱 Press Enter to return to main menu...")
        return
    
    # Step 2: Fingerprint authentication
    print("🔒 Place your finger on the sensor...")
    student_info = authenticate_fingerprint()
    
    if not student_info:
        print("❌ Authentication failed. Access denied.")
        set_led_idle()  # Return to idle on failure
        input("\n📱 Press Enter to return to main menu...")
        return
    
    # Display authentication success
    print(f"✅ Welcome: {student_info['name']} (ID: {student_info['student_id']})")
    
    # Step 3: Check current time status
    current_status = get_student_time_status(student_info['student_id'])
    print(f"📊 Current Status: {current_status}")
    
    if current_status == 'OUT' or current_status is None:
        # Student is timing IN - full verification required
        print("\n🟢 TIMING IN - Full verification required")
        
        # Step 4: License verification for TIME IN
        print("📄 Starting license verification...")
        image_path = auto_capture_license_rpi(reference_name=student_info['name'], 
                                           fingerprint_info=student_info)
        
        if not image_path:
            print("❌ License capture failed or cancelled.")
            set_led_idle()  # Return to idle on failure
            input("\n📱 Press Enter to return to main menu...")
            return
        
        # Process license
        ocr_preview = extract_text_from_image(image_path)
        ocr_lines = [line.strip() for line in ocr_preview.splitlines() if line.strip()]
        name_from_ocr, sim_score = find_best_line_match(student_info['name'], ocr_lines)
        result = licenseRead(image_path, student_info)
        
        # Prepare verification data
        verification_checks = {
            '🪖 Helmet': (True, 'VERIFIED'),
            '🔒 Fingerprint': (student_info['confidence'] > 50, f"VERIFIED ({student_info['confidence']}%)"),
            '🆔 License Detection': ("Driver's License Detected" in result.document_verified, 'VERIFIED' if "Driver's License Detected" in result.document_verified else 'FAILED'),
            '👤 Name Matching': (sim_score > 0.5 if sim_score else False, f"VERIFIED ({sim_score * 100:.1f}%)" if sim_score and sim_score > 0.5 else 'FAILED')
        }
        
        all_verified = all(status for status, _ in verification_checks.values())
        partial_verified = verification_checks['🪖 Helmet'][0] and verification_checks['🔒 Fingerprint'][0] and verification_checks['🆔 License Detection'][0]
        
        if all_verified:
            overall_status = "✅ TIME IN SUCCESSFUL"
            status_color = "🟢"
            
            # Record time in for successful verification
            if record_time_in(student_info):
                time_message = f"🟢 TIME IN recorded at {time.strftime('%H:%M:%S')}"
                # Set LED to success (green) for successful time in
                set_led_success(duration=5.0)  # Green for 5 seconds, then auto-return to idle
            else:
                time_message = "❌ Failed to record TIME IN"
                set_led_idle()  # Return to idle on database failure
            
            print(f"\n🕒 {time_message}")
            
        elif partial_verified:
            overall_status = "⚠️ PARTIAL VERIFICATION - TIME IN DENIED"
            status_color = "🟡"
            time_message = "❌ Time IN denied due to incomplete verification"
            set_led_idle()  # Return to idle on partial verification
        else:
            overall_status = "❌ VERIFICATION FAILED - TIME IN DENIED"
            status_color = "🔴"
            time_message = "❌ Time IN denied due to failed verification"
            set_led_idle()  # Return to idle on failed verification
        
        gui_message = f"""
TIME IN Verification Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Student: {student_info['name']}
🆔 Student ID: {student_info['student_id']}
📚 Course: {student_info['course']}
🪪 License: {student_info['license_number']}

{time_message}
Status: {overall_status}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
    else:
        # Student is timing OUT - only helmet + fingerprint required
        print("\n🔴 TIMING OUT - Helmet and fingerprint verification only")
        
        verification_checks = {
            '🪖 Helmet': (True, 'VERIFIED'),
            '🔒 Fingerprint': (student_info['confidence'] > 50, f"VERIFIED ({student_info['confidence']}%)")
        }
        
        # Record time out
        if record_time_out(student_info):
            overall_status = "✅ TIME OUT SUCCESSFUL"
            status_color = "🟢"
            time_message = f"🔴 TIME OUT recorded at {time.strftime('%H:%M:%S')}"
            # Set LED to success (green) for successful time out
            set_led_success(duration=5.0)  # Green for 5 seconds, then auto-return to idle
        else:
            overall_status = "❌ TIME OUT FAILED"
            status_color = "🔴"
            time_message = "❌ Failed to record TIME OUT"
            set_led_idle()  # Return to idle on failure
        
        print(f"\n🕒 {time_message}")
        
        gui_message = f"""
TIME OUT Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Student: {student_info['name']}
🆔 Student ID: {student_info['student_id']}
📚 Course: {student_info['course']}

{time_message}
Status: {overall_status}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
    
    verification_data = {
        'checks': verification_checks,
        'overall_status': overall_status,
        'status_color': status_color,
        'gui_message': gui_message
    }
    
    display_verification_result(student_info, verification_data)
    input("\n📱 Press Enter to return to main menu...")
    
    # Note: LED will either be in success state (auto-returning to idle) or already in idle state
    
# =================== VERIFICATION FUNCTIONS ===================

def verify_helmet_check():
    """Verify helmet is being worn"""
    if not verify_helmet():
        print("❌ Helmet verification failed. You must wear a FULL-FACE helmet.")
        return False
    print("✅ Helmet verification passed!")
    return True
