# controllers/guest.py - Updated with LED and Buzzer Integration

from services.license_reader import *
from services.helmet_infer import verify_helmet
from services.time_tracker import *
from services.led_control import *  
from services.buzzer_control import *
from utils.display_helpers import display_separator, display_verification_result
from utils.gui_helpers import show_results_gui, get_guest_info_gui, updated_guest_office_gui
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
    """Main guest verification workflow with LED and buzzer integration"""
    print("\n🎫 GUEST VERIFICATION SYSTEM")
    
    # Initialize buzzer system
    init_buzzer()
    
    # Set LED to processing and play processing sound
    set_led_processing()
    play_processing()
    
    # Step 1: Helmet verification
    print("🪖 Checking helmet...")
    if not verify_helmet():
        print("❌ Helmet verification failed")
        set_led_idle()
        play_failure()
        cleanup_buzzer()
        input("\n📱 Press Enter to return...")
        return
    
    print("✅ Helmet verified")
    
    # Step 2: Capture license
    print("📄 Starting license capture...")
    image_path = auto_capture_license_rpi()
    
    if not image_path:
        print("❌ License capture failed")
        set_led_idle()
        play_failure()
        cleanup_buzzer()
        input("\n📱 Press Enter to return...")
        return
    
    # Step 3: Extract name and check guest status
    ocr_preview = extract_text_from_image(image_path)
    ocr_lines = [line.strip() for line in ocr_preview.splitlines() if line.strip()]
    detected_name = extract_guest_name_from_license(ocr_lines)
    
    print(f"📄 Detected name: {detected_name}")
    
    current_status, guest_info = get_guest_time_status(detected_name)
    
    if current_status == 'IN':
        # Process TIME OUT
        print(f"✅ Found guest: {guest_info['name']} (Guest No: {guest_info['guest_number']}) ({guest_info['similarity_score']*100:.1f}% match)")
        print("🔴 TIMING OUT...")
        print("🛡️ Drive safe!")
        
        time_result = process_guest_time_out(guest_info)
        print(f"🕒 {time_result['message']}")
        
        if time_result['success']:
            set_led_success(duration=5.0)
            play_success()
        else:
            set_led_idle()
            play_failure()
        
    elif current_status == 'OUT' and guest_info is not None:
        # Process returning guest TIME IN
        print(f"✅ Returning guest: {guest_info['name']} (Guest No: {guest_info['guest_number']}) ({guest_info['similarity_score']*100:.1f}% match)")
        print("🟢 TIMING IN...")
        
        # Get updated office info
        updated_guest_info = updated_guest_office_gui(guest_info['name'], guest_info.get('office', 'CSS Office'))
        
        if not updated_guest_info:
            print("❌ Office update cancelled")
            set_led_idle()
            play_failure()
            cleanup_buzzer()
            input("\n📱 Press Enter to return...")
            return
        
        existing_guest_info = {
            'name': updated_guest_info['name'],
            'plate_number': guest_info['plate_number'],
            'office': updated_guest_info['office']
        }
        
        # Simplified guest data for verification (no unnecessary fields)
        guest_data_for_license = {
            'name': existing_guest_info['name'],
            'plate_number': existing_guest_info['plate_number'],
            'office': existing_guest_info['office'],
            'is_guest': True
        }
        
        # Use the simplified guest verification flow
        is_guest_verified = complete_guest_verification_flow(
            image_path=image_path,
            guest_info=guest_data_for_license,
            helmet_verified=True
        )
        
        if is_guest_verified:
            # Store/update guest info in guests table
            store_guest_in_database(existing_guest_info)
            
            time_result = process_guest_time_in(existing_guest_info)
            print(f"🕒 {time_result['message']}")
            
            if time_result['success']:
                set_led_success(duration=5.0)
                play_success()
            else:
                set_led_idle()
                play_failure()
        else:
            print("❌ Guest verification failed")
            set_led_idle()
            play_failure()
        
    else:
        # New guest TIME IN
        print("🟢 New guest - TIMING IN...")
        
        guest_info_input = get_guest_info_gui(detected_name)
        
        if not guest_info_input:
            print("❌ Guest info cancelled")
            set_led_idle()
            play_failure()
            cleanup_buzzer()
            input("\n📱 Press Enter to return...")
            return
        
        print(f"✅ Guest info: {guest_info_input['name']} | Guest No: {guest_info_input['plate_number']} | {guest_info_input['office']}")
        
        # Simplified guest data for verification (no unnecessary fields)
        guest_data_for_license = {
            'name': guest_info_input['name'],
            'plate_number': guest_info_input['plate_number'],
            'office': guest_info_input['office'],
            'is_guest': True
        }
        
        # Use the simplified guest verification flow
        is_guest_verified = complete_guest_verification_flow(
            image_path=image_path,
            guest_info=guest_data_for_license,
            helmet_verified=True
        )
        
        if is_guest_verified:
            # Store new guest info in guests table
            store_guest_in_database(guest_info_input)
            
            time_result = process_guest_time_in(guest_info_input)
            print(f"🕒 {time_result['message']}")
            
            if time_result['success']:
                set_led_success(duration=5.0)
                play_success()
            else:
                set_led_idle()
                play_failure()
        else:
            print("❌ Guest verification failed")
            set_led_idle()
            play_failure()
    
    # Clean up buzzer before returning
    cleanup_buzzer()
    input("\n📱 Press Enter to return...")

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

