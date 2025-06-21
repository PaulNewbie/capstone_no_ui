# controllers/guest.py - Cleaned and Optimized

from services.license_reader import (
    auto_capture_license_rpi, 
    extract_text_from_image, 
    extract_guest_name_from_license,
    complete_guest_verification_flow
)
from services.helmet_infer import verify_helmet
from services.led_control import *  
from utils.gui_helpers import show_results_gui, get_guest_info_gui, updated_guest_office_gui

# Import database functions
from database.unified_db import db
from database.db_operations import record_guest_time_in, record_guest_time_out

import difflib
import time

def guest_verification():
    """Main guest verification workflow"""
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
    detected_name = extract_guest_name_from_license_image(image_path)
    print(f"📄 Detected name: {detected_name}")
    
    current_status, guest_info = get_guest_time_status(detected_name)
    
    if current_status == 'IN':
        # Process TIME OUT
        _process_guest_time_out(guest_info, image_path)
    elif current_status == 'OUT' and guest_info is not None:
        # Process returning guest TIME IN
        _process_returning_guest_time_in(guest_info, image_path)
    else:
        # New guest TIME IN
        _process_new_guest_time_in(detected_name, image_path)
    
    input("\n📱 Press Enter to return...")

def extract_guest_name_from_license_image(image_path: str) -> str:
    """Simple and reliable guest name extraction - returns SURNAME, FIRSTNAME MIDDLENAME format"""
    try:
        import re
        ocr_text = extract_text_from_image(image_path)
        lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
        
        # Debug: Show what we're working with
        print("Debug: Checking lines for name:")
        for i, line in enumerate(lines[:15]):
            print(f"  Line {i}: {line}")
        
        # Check first 15 lines only
        for line in lines[:15]:
            original_line = line.strip()
            line_clean = line.upper().strip()
            
            # Remove common OCR artifacts: leading numbers, dots, special chars
            line_clean = re.sub(r'^[\d\.\-\s]+', '', line_clean)
            
            # Skip empty lines after cleaning
            if not line_clean or len(line_clean) < 7:
                continue
            
            # Skip if doesn't have exactly one comma
            if line_clean.count(',') != 1:
                continue
            
            # ADDRESS PATTERNS TO SKIP
            address_indicators = [
                'BLK', 'BLOCK', 'LOT', 'PHASE', 'PH', 
                'STREET', 'ST', 'ROAD', 'RD', 'AVENUE', 'AVE',
                'BARANGAY', 'BRGY', 'CITY', 'PROVINCE',
                'UNIT', 'BLDG', 'BUILDING', 'FLOOR', 'FLR',
                'SUBDIVISION', 'SUBD', 'VILLAGE', 'VILL',
                'RESIDENCIA', 'RESIDENCE', 'APARTMENT', 'APT',
                'CONDO', 'CONDOMINIUM', 'TOWNHOUSE',
                'ZIP', 'POSTAL'
            ]
            
            # Check if line contains address indicators
            contains_address = any(indicator in line_clean.split() for indicator in address_indicators)
            if contains_address:
                print(f"  Skipping address line: {line_clean}")
                continue
            
            # Skip lines with obvious document keywords
            doc_keywords = [
                'REPUBLIC', 'PHILIPPINES', 'DEPARTMENT', 'TRANSPORTATION', 
                'LICENSE', 'DRIVER', 'ADDRESS', 'NATIONALITY', 'OFFICE',
                'EXPIRATION', 'REGISTRATION', 'RESTRICTION', 'CONDITION'
            ]
            if any(keyword in line_clean for keyword in doc_keywords):
                print(f"  Skipping document line: {line_clean}")
                continue
            
            # Check for number patterns common in addresses
            # Like "123 STREET" or "BLOCK 13" but not in names
            if re.search(r'\b\d{2,}\b', line_clean):  # Contains numbers with 2+ digits
                print(f"  Skipping line with multi-digit numbers: {line_clean}")
                continue
            
            try:
                # Split by comma
                parts = line_clean.split(',')
                if len(parts) != 2:
                    continue
                    
                lastname = parts[0].strip()
                firstname = parts[1].strip()
                
                # Remove any remaining single digits or special chars
                # But keep spaces and letters
                lastname_clean = re.sub(r'[^A-Z\s]', '', lastname).strip()
                firstname_clean = re.sub(r'[^A-Z\s]', '', firstname).strip()
                
                # Additional validation for names
                # Names shouldn't be too short or too long
                if (not lastname_clean or not firstname_clean or
                    len(lastname_clean) < 2 or len(firstname_clean) < 2 or
                    len(lastname_clean) > 20 or len(firstname_clean) > 30):
                    continue
                
                # Check if both parts are valid names (only letters and spaces)
                if (lastname_clean.replace(' ', '').isalpha() and 
                    firstname_clean.replace(' ', '').isalpha()):
                    
                    # Additional check: Names typically don't have more than 3 words
                    if (len(lastname_clean.split()) <= 3 and 
                        len(firstname_clean.split()) <= 4):
                        
                        print(f"  Found name: {lastname_clean}, {firstname_clean}")
                        # Return in SURNAME, FIRSTNAME MIDDLENAME format (all uppercase)
                        return f"{lastname_clean}, {firstname_clean}"
                    
            except Exception as e:
                print(f"  Error processing line '{line}': {e}")
                continue
        
        print("  No valid name found, returning 'Guest'")
        return "Guest"
        
    except Exception as e:
        print(f"Error in extract_guest_name_from_license_image: {e}")
        return "Guest"
              
def get_guest_time_status(detected_name, plate_number=None):
    """Get current time status of guest"""
    try:
        # Get all people currently inside
        people_inside = db.get_people_currently_inside('GUEST')
        
        # Check people currently inside first
        for person in people_inside:
            guest_name = person['person_name']
            similarity = _calculate_name_similarity(detected_name, guest_name)
            
            if similarity > 0.6:
                guest_id = person['person_id']
                guest_details = db.get_guest(guest_id=guest_id)
                
                if guest_details:
                    guest_info = {
                        'name': guest_details['full_name'],
                        'student_id': guest_id,
                        'plate_number': guest_details['plate_number'],
                        'office': guest_details['office_visiting'],
                        'current_status': 'IN',
                        'similarity_score': similarity
                    }
                    return 'IN', guest_info
        
        # Check recent records for returning guests
        recent_records = db.get_time_records(person_type='GUEST', limit=50)
        guest_records = {}
        
        for record in recent_records:
            guest_id = record['person_id']
            if guest_id not in guest_records:
                guest_records[guest_id] = {
                    'name': record['person_name'],
                    'last_action': record['action'],
                    'timestamp': record['timestamp']
                }
        
        # Find best match among recent guests
        best_match = None
        highest_similarity = 0.0
        
        for guest_id, record in guest_records.items():
            guest_name = record['name']
            similarity = _calculate_name_similarity(detected_name, guest_name)
            
            if similarity > highest_similarity and similarity > 0.6:
                highest_similarity = similarity
                guest_details = db.get_guest(guest_id=guest_id)
                
                if guest_details:
                    best_match = {
                        'name': guest_details['full_name'],
                        'student_id': guest_id,
                        'plate_number': guest_details['plate_number'],
                        'office': guest_details['office_visiting'],
                        'current_status': record['last_action'],
                        'similarity_score': similarity
                    }
        
        if best_match:
            return best_match['current_status'], best_match
        
        return None, None
        
    except Exception as e:
        print(f"❌ Error checking guest status: {e}")
        return None, None

def _calculate_name_similarity(detected_name: str, guest_name: str) -> float:
    """Calculate similarity between two names"""
    similarity = difflib.SequenceMatcher(None, detected_name.upper(), guest_name.upper()).ratio()
    
    # Boost for substring matches
    if (detected_name.upper() in guest_name.upper() or 
        guest_name.upper() in detected_name.upper()):
        similarity = max(similarity, 0.8)
    
    return similarity

def _process_guest_time_out(guest_info, image_path):
    """Process guest time out"""
    print(f"✅ Found guest: {guest_info['name']} ({guest_info['similarity_score']*100:.1f}% match)")
    print("🔴 TIMING OUT...")
    print("🛡️ Drive safe!")
    
    time_result = _record_guest_time_out(guest_info)
    print(f"🕒 {time_result['message']}")
    
    if time_result['success']:
        set_led_success(duration=5.0)
    else:
        set_led_idle()

def _process_returning_guest_time_in(guest_info, image_path):
    """Process returning guest time in"""
    print(f"✅ Returning guest: {guest_info['name']} ({guest_info['similarity_score']*100:.1f}% match)")
    print("🟢 TIMING IN...")
    
    # Get updated office info
    updated_guest_info = updated_guest_office_gui(guest_info['name'], guest_info.get('office', 'CSS Office'))
    
    if not updated_guest_info:
        print("❌ Office update cancelled")
        set_led_idle()
        return
    
    guest_data = {
        'name': updated_guest_info['name'],
        'plate_number': guest_info['plate_number'],
        'office': updated_guest_info['office'],
        'is_guest': True
    }
    
    # Verify license
    is_verified = complete_guest_verification_flow(
        image_path=image_path,
        guest_info=guest_data,
        helmet_verified=True
    )
    
    if is_verified:
        time_result = _record_guest_time_in(guest_data)
        print(f"🕒 {time_result['message']}")
        
        if time_result['success']:
            set_led_success(duration=5.0)
        else:
            set_led_idle()
    else:
        print("❌ Guest verification failed")
        set_led_idle()

def _process_new_guest_time_in(detected_name, image_path):
    """Process new guest time in"""
    print("🟢 New guest - TIMING IN...")
    
    guest_info_input = get_guest_info_gui(detected_name)
    
    if not guest_info_input:
        print("❌ Guest info cancelled")
        set_led_idle()
        return
    
    print(f"✅ Guest info: {guest_info_input['name']} | {guest_info_input['plate_number']} | {guest_info_input['office']}")
    
    guest_data = {
        'name': guest_info_input['name'],
        'plate_number': guest_info_input['plate_number'],
        'office': guest_info_input['office'],
        'is_guest': True
    }
    
    # Verify license
    is_verified = complete_guest_verification_flow(
        image_path=image_path,
        guest_info=guest_data,
        helmet_verified=True
    )
    
    if is_verified:
        time_result = _record_guest_time_in(guest_data)
        print(f"🕒 {time_result['message']}")
        
        if time_result['success']:
            set_led_success(duration=5.0)
        else:
            set_led_idle()
    else:
        print("❌ Guest verification failed")
        set_led_idle()

def _record_guest_time_in(guest_info):
    """Record guest time in"""
    try:
        success = record_guest_time_in(guest_info)
        
        if success:
            return {
                'success': True,
                'message': f"✅ TIME IN SUCCESSFUL - {time.strftime('%H:%M:%S')}"
            }
        else:
            return {
                'success': False,
                'message': "❌ Failed to record TIME IN"
            }
    except Exception as e:
        print(f"❌ Error processing guest time in: {e}")
        return {
            'success': False,
            'message': f"❌ Error: {e}"
        }

def _record_guest_time_out(guest_info):
    """Record guest time out"""
    try:
        success = record_guest_time_out(guest_info)
        
        if success:
            return {
                'success': True,
                'message': f"✅ TIME OUT SUCCESSFUL - {time.strftime('%H:%M:%S')}"
            }
        else:
            return {
                'success': False,
                'message': "❌ Failed to record TIME OUT"
            }
    except Exception as e:
        print(f"❌ Error processing guest time out: {e}")
        return {
            'success': False,
            'message': f"❌ Error: {e}"
        }
