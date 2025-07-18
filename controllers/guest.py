# controllers/guest.py - With security code verification for timeout and retake for timing in

from services.license_reader import *
from services.helmet_infer import verify_helmet
from services.led_control import *  
from services.buzzer_control import *
from services.rpi_camera import force_camera_cleanup
from utils.display_helpers import display_separator, display_verification_result
from utils.gui_helpers import show_results_gui, get_guest_info_gui, updated_guest_office_gui
from utils.timeout_security import timeout_security_verification  # Import security verification
import difflib
import time

from database.db_operations import (
    add_guest,
    get_guest_time_status,
    get_guest_from_database,
    create_guest_time_data, 
    process_guest_time_in,
    process_guest_time_out
)

def guest_verification():
    """Main guest verification with GUI"""
    print("\n🎫 GUEST VERIFICATION")
    print("🖥️ Opening GUI interface...")
    
    # Import GUI here to avoid circular imports
    from ui.guest_gui import GuestVerificationGUI
    
    # No cleanup needed at start
    
    # Create and run GUI
    gui = GuestVerificationGUI(run_guest_verification_with_gui)
    gui.run()

def run_guest_verification_with_gui(status_callback):
    """Run guest verification steps with GUI status updates - Security for timeout, retake for timing in"""
    
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
            # No camera cleanup needed
            return {'verified': False, 'reason': 'Helmet verification failed'}
        
        # Step 2: License capture and guest info (with retake loop for new guests)
        while True:  # Loop to handle retake requests
            # License capture
            status_callback({'current_step': '📄 Capturing license... (Check terminal for camera)'})
            status_callback({'license_status': 'PROCESSING'})
            
            print("\n" + "="*60)
            print("📄 LICENSE CAPTURE (Terminal Camera)")
            print("="*60)
            
            # No cleanup before license capture - smart cleanup handles it
            image_path = auto_capture_license_rpi()
            
            if not image_path:
                status_callback({'license_status': 'FAILED'})
                status_callback({'current_step': '❌ License capture failed'})
                set_led_idle()
                play_failure()
                cleanup_buzzer()
                # No camera cleanup needed
                return {'verified': False, 'reason': 'License capture failed'}
            
            status_callback({'license_status': 'DETECTED'})
            
            # Step 3: Extract name and check guest status
            status_callback({'current_step': '🔍 Processing license information...'})
            
            ocr_preview = extract_text_from_image(image_path)
            ocr_lines = [line.strip() for line in ocr_preview.splitlines() if line.strip()]
            detected_name = extract_guest_name_from_license(ocr_lines)
            
            print(f"📄 Detected name: {detected_name}")
            
            current_status, guest_info = get_guest_time_status(detected_name)
            
            if current_status == 'IN':
                # TIMEOUT PROCESS - Use security code verification (NO retake here)
                print(f"🔍 Found guest '{guest_info['name']}' currently IN")
                print(f"📄 Detected name: '{detected_name}'")
                print(f"🤔 Match confidence: {guest_info.get('similarity_score', 0)*100:.1f}%")
                
                status_callback({'current_step': '🔐 Security verification required for timeout...'})
                
                # Show guest info
                status_callback({
                    'guest_info': {
                        'name': guest_info['name'],
                        'guest_number': guest_info['guest_number'],
                        'plate_number': guest_info['plate_number'],
                        'office': guest_info['office'],
                        'status': 'GUEST TIMEOUT - SECURITY CHECK'
                    }
                })
                
                # SECURITY CODE VERIFICATION - No confirmation dialog, straight to security
                security_verified = timeout_security_verification(guest_info)
                
                if security_verified:
                    # Security code verified - proceed with TIME OUT
                    print("✅ Security code verified - proceeding with TIME OUT")
                    
                    status_callback({'current_step': '🔍 Verifying license for timeout...'})
                    
                    # Verify guest and process time out
                    is_guest_verified = complete_guest_verification_flow(
                        image_path=image_path,
                        guest_info=guest_info,
                        helmet_verified=True
                    )
                    
                    if is_guest_verified:
                        time_result = process_guest_time_out(guest_info)
                        
                        if time_result['success']:
                            timestamp = time.strftime('%H:%M:%S')
                            status_callback({'current_step': f'✅ TIME OUT recorded at {timestamp}'})
                            set_led_success(duration=5.0)
                            play_success()
                            
                            # Show verification summary
                            status_callback({
                                'verification_summary': {
                                    'helmet': True,
                                    'license': True
                                }
                            })
                            
                            result = {
                                'verified': True,
                                'name': guest_info['name'],
                                'time_action': 'OUT',
                                'timestamp': timestamp,
                                'guest_number': guest_info['guest_number']
                            }
                        else:
                            status_callback({'current_step': '❌ Failed to record TIME OUT'})
                            set_led_idle()
                            play_failure()
                            result = {'verified': False, 'reason': 'Failed to record TIME OUT'}
                    else:
                        status_callback({'current_step': '❌ Guest verification failed'})
                        set_led_idle()
                        play_failure()
                        result = {'verified': False, 'reason': 'License verification failed'}
                        
                    cleanup_buzzer()
                    return result
                
                else:
                    # Security verification failed or cancelled
                    print("❌ Security verification failed or cancelled")
                    status_callback({'current_step': '❌ Security verification failed - Timeout DENIED'})
                    safe_delete_temp_file(image_path)
                    set_led_idle()
                    play_failure()
                    cleanup_buzzer()
                    return {'verified': False, 'reason': 'Security verification failed'}
            
            else:
                # NEW GUEST TIME IN - This is where the retake functionality works
                status_callback({
                    'guest_info': {
                        'name': detected_name if detected_name != "Guest" else "New Guest",
                        'status': 'NEW GUEST - REGISTRATION'
                    }
                })
                
                status_callback({'current_step': '📝 Please provide guest information...'})
                
                # Get guest info (using GUI dialog) - HANDLES RETAKE FROM REGISTRATION FORM
                guest_info_input = get_guest_info_gui(detected_name)
                
                # Handle the different return values
                if guest_info_input == 'retake':
                    # User wants to retake license - clean up current image and continue loop
                    print("📷 User requested license retake from registration form")
                    status_callback({'current_step': '🔄 Retaking license scan...'})
                    safe_delete_temp_file(image_path)
                    continue  # Go back to the beginning of the while loop
                    
                elif not guest_info_input:
                    # User cancelled
                    status_callback({'current_step': '❌ Guest registration cancelled'})
                    safe_delete_temp_file(image_path)
                    set_led_idle()
                    play_failure()
                    cleanup_buzzer()
                    return {'verified': False, 'reason': 'Guest registration cancelled'}
                
                # User provided valid guest info - continue with verification
                # Update guest info display
                status_callback({
                    'guest_info': {
                        'name': guest_info_input['name'],
                        'plate_number': guest_info_input['plate_number'],
                        'office': guest_info_input['office'],
                        'status': 'NEW GUEST - REGISTERED'
                    }
                })
                
                # Verify guest
                guest_data_for_license = {
                    'name': guest_info_input['name'],
                    'plate_number': guest_info_input['plate_number'],
                    'office': guest_info_input['office'],
                    'is_guest': True
                }
                
                is_guest_verified = complete_guest_verification_flow(
                    image_path=image_path,
                    guest_info=guest_data_for_license,
                    helmet_verified=True
                )
                
                if is_guest_verified:
                    store_guest_in_database(guest_info_input)
                    time_result = process_guest_time_in(guest_info_input)
                    
                    if time_result['success']:
                        timestamp = time.strftime('%H:%M:%S')
                        status_callback({'current_step': f'✅ TIME IN recorded at {timestamp}'})
                        set_led_success(duration=5.0)
                        play_success()
                        
                        # Show verification summary
                        status_callback({
                            'verification_summary': {
                                'helmet': True,
                                'license': True
                            }
                        })
                        
                        result = {
                            'verified': True,
                            'name': guest_info_input['name'],
                            'time_action': 'IN',
                            'timestamp': timestamp,
                            'office': guest_info_input['office']
                        }
                    else:
                        status_callback({'current_step': '❌ Failed to record TIME IN'})
                        set_led_idle()
                        play_failure()
                        result = {'verified': False, 'reason': 'Failed to record TIME IN'}
                else:
                    status_callback({'current_step': '❌ Guest verification failed'})
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
              
def store_guest_in_database(guest_info):
    """Store or update guest information in the guests table"""
    try:
        guest_data = {
            'full_name': guest_info['name'],
            'plate_number': guest_info['plate_number'],
            'office_visiting': guest_info['office']
        }
        
        guest_number = add_guest(guest_data)
        
        if guest_number:
            print(f"✅ Guest record saved (Guest No: {guest_number})")
            return True
        else:
            print(f"❌ Failed to save guest record")
            return False
            
    except Exception as e:
        print(f"❌ Error storing guest in database: {e}")
        return False
