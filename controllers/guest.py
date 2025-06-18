# controllers/guest.py - Simplified Guest Controller with Clean Logging

from services.license_reader import *
from services.helmet_infer import verify_helmet
from services.time_tracker import *
from services.led_control import *  
from utils.display_helpers import display_separator, display_verification_result
from utils.gui_helpers import show_results_gui, get_guest_info_gui, updated_guest_office_gui
import difflib
import time

def guest_verification():
    """Main guest verification workflow - simplified logging"""
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
        print(f"✅ Found guest: {guest_info['name']} ({guest_info['similarity_score']*100:.1f}% match)")
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
        print(f"✅ Returning guest: {guest_info['name']} ({guest_info['similarity_score']*100:.1f}% match)")
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
        
        guest_data_for_license = {
            'name': existing_guest_info['name'],
            'student_id': 'GUEST',
            'course': 'N/A',
            'license_number': 'N/A',
            'license_expiration': 'N/A',
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
        
        print(f"✅ Guest info: {guest_info_input['name']} | {guest_info_input['plate_number']} | {guest_info_input['office']}")
        
        guest_data_for_license = {
            'name': guest_info_input['name'],
            'student_id': 'GUEST',
            'course': 'N/A',
            'license_number': 'N/A',
            'license_expiration': 'N/A',
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

def extract_guest_name_from_license(ocr_lines):
    """Extract guest name from license OCR - simplified"""
    filter_keywords = [
        'ROAD', 'STREET', 'AVENUE', 'DISTRICT', 'CITY', 'PROVINCE', 'MARILAO', 'BULACAN',
        'BARANGAY', 'REPUBLIC', 'PHILIPPINES', 'TRANSPORTATION', 
        'DRIVER', 'LICENSE', 'NATIONALITY', 'ADDRESS', 'WEIGHT', 'HEIGHT'
    ]
    
    potential_names = []
    
    for line in ocr_lines:
        line_clean = line.strip().upper()
        
        # Skip invalid lines
        if (not line_clean or len(line_clean) < 5 or len(line_clean) > 50 or
            any(keyword in line_clean for keyword in filter_keywords) or
            any(char.isdigit() for char in line_clean)):
            continue
        
        # Look for name patterns
        if line_clean.replace(" ", "").replace(",", "").isalpha() and " " in line_clean:
            score = 0
            if "," in line_clean: score += 10  # Last, First format
            word_count = len(line_clean.split())
            if 2 <= word_count <= 4: score += 5
            if 10 <= len(line_clean) <= 30: score += 3
            potential_names.append((line_clean, score))
    
    if potential_names:
        potential_names.sort(key=lambda x: x[1], reverse=True)
        return potential_names[0][0]
    
    return "Guest"

def get_guest_time_status(detected_name, plate_number=None):
    """Get current time status of guest - simplified logging"""
    try:
        import sqlite3
        from difflib import SequenceMatcher
        
        conn = sqlite3.connect("database/time_tracking.db")
        cursor = conn.cursor()
        
        # Get latest record for each guest
        cursor.execute("""
            SELECT student_name, student_id, status, date, time,
                   ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY date DESC, time DESC) as row_num
            FROM time_records 
            WHERE student_id LIKE 'GUEST_%'
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
            guest_name = record[0]
            
            # Calculate similarity
            similarity = SequenceMatcher(None, detected_name.upper(), guest_name.upper()).ratio()
            
            # Boost for substring matches
            if (detected_name.upper() in guest_name.upper() or 
                guest_name.upper() in detected_name.upper()):
                similarity = max(similarity, 0.8)
            
            # Boost for plate match if provided
            if plate_number:
                guest_plate = record[1].replace('GUEST_', '')
                if plate_number.upper() == guest_plate.upper():
                    similarity = max(similarity, 0.9)
            
            if similarity > highest_similarity and similarity > 0.6:
                highest_similarity = similarity
                best_match = record
        
        if best_match:
            guest_info = {
                'name': best_match[0],
                'student_id': best_match[1],
                'plate_number': best_match[1].replace('GUEST_', ''),
                'office': 'Previous Visit',
                'current_status': best_match[2],
                'last_date': best_match[3],
                'last_time': best_match[4],
                'similarity_score': highest_similarity
            }
            
            return best_match[2], guest_info
        
        return None, None
        
    except Exception as e:
        print(f"❌ Error checking guest status: {e}")
        return None, None

def create_guest_time_data(guest_info):
    """Create standardized guest data for time tracking"""
    return {
        'name': guest_info['name'],
        'student_id': f"GUEST_{guest_info['plate_number']}",
        'course': f"Guest - {guest_info['office']}",
        'license_number': guest_info['plate_number'],
        'confidence': 100
    }

def process_guest_time_in(guest_info):
    """Process guest time in - simplified"""
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

def process_guest_time_out(guest_info):
    """Process guest time out - simplified"""
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
