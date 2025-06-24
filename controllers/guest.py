# controllers/guest.py - Updated for new database structure (keeps existing imports)

from services.license_reader import *
from services.helmet_infer import verify_helmet
from services.time_tracker import *
from services.led_control import *  
from utils.display_helpers import display_separator, display_verification_result
from utils.gui_helpers import show_results_gui, get_guest_info_gui, updated_guest_office_gui
import difflib
import time

def guest_verification():
    """Main guest verification workflow - updated for new database"""
    print("\n🎫 GUEST VERIFICATION SYSTEM")
    
    set_led_processing()
    
    # Step 1: Helmet verification
    print("🪖 Checking helmet...")
    if not verify_helmet():
        print("❌ Helmet verification failed")
        set_led_idle()
        input("\n📱 Press Enter to return...")
        return
    
    print("✅ Helmet verified")
    
    # Step 2: Capture license
    print("📄 Starting license capture...")
    image_path = auto_capture_license_rpi()
    
    if not image_path:
        print("❌ License capture failed")
        set_led_idle()
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
        else:
            set_led_idle()
        
    elif current_status == 'OUT' and guest_info is not None:
        # Process returning guest TIME IN
        print(f"✅ Returning guest: {guest_info['name']} (Guest No: {guest_info['guest_number']}) ({guest_info['similarity_score']*100:.1f}% match)")
        print("🟢 TIMING IN...")
        
        # Get updated office info
        updated_guest_info = updated_guest_office_gui(guest_info['name'], guest_info.get('office', 'CSS Office'))
        
        if not updated_guest_info:
            print("❌ Office update cancelled")
            set_led_idle()
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
            else:
                set_led_idle()
        else:
            print("❌ Guest verification failed")
            set_led_idle()
        
    else:
        # New guest TIME IN
        print("🟢 New guest - TIMING IN...")
        
        guest_info_input = get_guest_info_gui(detected_name)
        
        if not guest_info_input:
            print("❌ Guest info cancelled")
            set_led_idle()
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
            else:
                set_led_idle()
        else:
            print("❌ Guest verification failed")
            set_led_idle()
    
    input("\n📱 Press Enter to return...")

def store_guest_in_database(guest_info):
    """Store or update guest information in the guests table"""
    try:
        from database.db_operations import add_guest
        
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

def get_guest_time_status(detected_name, plate_number=None):
    """Get current time status of guest - updated for new database"""
    try:
        import sqlite3
        from difflib import SequenceMatcher
        
        # Use the new centralized database
        conn = sqlite3.connect("database/motorpass.db")
        cursor = conn.cursor()
        
        # Get latest record for each guest from time_tracking
        cursor.execute("""
            SELECT user_id, user_name, action, date, time,
                   ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY timestamp DESC) as row_num
            FROM time_tracking 
            WHERE user_type = 'GUEST'
        """)
        
        all_records = cursor.fetchall()
        conn.close()
        
        # Filter to latest records only
        latest_records = [record for record in all_records if record[5] == 1]
        
        if not latest_records:
            return None, None
        
        print(f"🔍 Checking against {len(latest_records)} guest records...")
        
        # Find best name match
        best_match = None
        highest_similarity = 0.0
        
        for record in latest_records:
            guest_name = record[1]  # user_name
            
            # Calculate similarity
            similarity = SequenceMatcher(None, detected_name.upper(), guest_name.upper()).ratio()
            
            # Boost for substring matches
            if (detected_name.upper() in guest_name.upper() or 
                guest_name.upper() in detected_name.upper()):
                similarity = max(similarity, 0.8)
            
            # Boost for plate match if provided
            if plate_number:
                guest_plate = record[0].replace('GUEST_', '')  # user_id
                if plate_number.upper() == guest_plate.upper():
                    similarity = max(similarity, 0.9)
            
            if similarity > highest_similarity and similarity > 0.6:
                highest_similarity = similarity
                best_match = record
        
        if best_match:
            # Get additional guest info from guests table if needed
            guest_db_info = get_guest_from_database(
                plate_number=best_match[0].replace('GUEST_', ''),
                name=best_match[1]
            )
            
            guest_info = {
                'name': best_match[1],  # user_name
                'student_id': best_match[0],  # user_id (GUEST_PLATE format)
                'guest_number': best_match[0].replace('GUEST_', ''),  # Just the plate number
                'plate_number': best_match[0].replace('GUEST_', ''),
                'office': guest_db_info['office'] if guest_db_info else 'Previous Visit',
                'current_status': best_match[2],  # action (IN/OUT)
                'last_date': best_match[3],
                'last_time': best_match[4],
                'similarity_score': highest_similarity
            }
            
            return best_match[2], guest_info  # action (IN/OUT), guest_info
        
        return None, None
        
    except Exception as e:
        print(f"❌ Error checking guest status: {e}")
        return None, None

def get_guest_from_database(plate_number=None, name=None):
    """Retrieve guest information from guests table"""
    try:
        from database.db_operations import get_guest_by_plate, get_guest_by_name_and_plate
        
        if plate_number and name:
            guest_data = get_guest_by_name_and_plate(name, plate_number)
        elif plate_number:
            guest_data = get_guest_by_plate(plate_number)
        else:
            return None
        
        if guest_data:
            return {
                'guest_id': guest_data['guest_id'],
                'name': guest_data['full_name'],
                'plate_number': guest_data['plate_number'],
                'office': guest_data['office_visiting'],
                'created_date': guest_data['created_date'],
                'last_visit': guest_data.get('last_visit', guest_data['created_date'])
            }
        
        return None
        
    except Exception as e:
        print(f"❌ Error retrieving guest from database: {e}")
        return None

def create_guest_time_data(guest_info):
    """Create standardized guest data for time tracking - simplified for guests"""
    return {
        'name': guest_info['name'],
        'unified_id': f"GUEST_{guest_info['plate_number']}",
        'student_id': f"GUEST_{guest_info['plate_number']}",
        'user_type': 'GUEST',
        'full_name': guest_info['name'],
        'confidence': 100
    }

def process_guest_time_in(guest_info):
    """Process guest time in - using new database functions"""
    try:
        from database.db_operations import record_time_in
        
        guest_time_data = create_guest_time_data(guest_info)
        
        if record_time_in(guest_time_data):
            return {
                'success': True,
                'status': "✅ GUEST TIME IN SUCCESSFUL",
                'message': f"✅ TIME IN SUCCESSFUL - {time.strftime('%H:%M:%S')}",
                'color': "🟢"
            }
        else:
            return {
                'success': False,
                'status': "❌ TIME IN FAILED",
                'message': "❌ Failed to record TIME IN",
                'color': "🔴"
            }
            
    except ImportError:
        print(f"❌ Error TIME OUT!!!: {e}")
        return None
        

def process_guest_time_out(guest_info):
    """Process guest time out - using new database functions"""
    try:
        from database.db_operations import record_time_out
        
        guest_time_data = create_guest_time_data(guest_info)
        
        if record_time_out(guest_time_data):
            return {
                'success': True,
                'status': "✅ GUEST TIME OUT SUCCESSFUL",
                'message': f"✅ TIME OUT SUCCESSFUL - {time.strftime('%H:%M:%S')}",
                'color': "🟢"
            }
        else:
            return {
                'success': False,
                'status': "❌ TIME OUT FAILED",
                'message': "❌ Failed to record TIME OUT",
                'color': "🔴"
            }
            
    except ImportError:
        print(f"❌ Error TIME OUT!!!: {e}")
        return None
