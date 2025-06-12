# controllers/guest.py - Updated for RPi Camera 3

from services.license_reader import *
from services.helmet_infer import verify_helmet
from services.time_tracker import *
from utils.display_helpers import display_separator, display_verification_result
from utils.gui_helpers import show_results_gui, get_guest_info_gui, updated_guest_office_gui
import tkinter as tk
from tkinter import simpledialog, messagebox
import difflib
import time

def guest_verification():
    """Main guest verification workflow - FIXED VERSION"""
    print("\n👤 GUEST VERIFICATION SYSTEM")
    
    # Step 1: Helmet verification (always required)
    if not verify_helmet():
        input("\n📱 Press Enter to return to main menu...")
        return
    
    # Step 2: Capture license
    print("📄 Starting license capture...")
    image_path = auto_capture_license_rpi()
    
    if not image_path:
        print("❌ License capture failed or cancelled.")
        input("\n📱 Press Enter to return to main menu...")
        return
    
    # Step 3: Extract name from license
    ocr_preview = extract_text_from_image(image_path)
    ocr_lines = [line.strip() for line in ocr_preview.splitlines() if line.strip()]
    detected_name = extract_guest_name_from_license(ocr_lines)
    
    print(f"📄 Detected name: {detected_name}")
    
    # Step 4: Check guest's current status
    current_status, guest_info = get_guest_time_status(detected_name)
    
    if current_status == 'IN':
        # Guest is currently timed IN - Process TIME OUT
        print(f"\n✅ Found currently timed-in guest: {guest_info['name']}")
        print(f"🚗 Plate: {guest_info['plate_number']}")
        print(f"📅 Timed in: {guest_info['last_date']} at {guest_info['last_time']}")
        print(f"🎯 Match confidence: {guest_info['similarity_score']*100:.1f}%")
        print("\n🔴 PROCESSING TIME OUT...")
        
        # Process time out
        time_result = process_guest_time_out(guest_info)
        print(f"\n🕒 {time_result['message']}")
        
        # Create verification data for display
        verification_checks = {
            '🪖 Helmet': (True, 'VERIFIED'),
            '🆔 License Detection': (True, 'VERIFIED'),
            '👤 Name Match': (True, f"MATCHED ({guest_info['similarity_score']*100:.1f}%)")
        }
        
        gui_message = f"""
GUEST TIME OUT COMPLETE!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Guest: {guest_info['name']}
🚗 Plate: {guest_info['plate_number']}
📅 Original Time In: {guest_info['last_date']} {guest_info['last_time']}
🎯 Match Confidence: {guest_info['similarity_score']*100:.1f}%

{time_result['message']}
Status: {time_result['status']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        guest_data = {
            'name': guest_info['name'],
            'plate_number': guest_info['plate_number'],
            'office': guest_info.get('office', 'Previous Visit'),
            'is_guest': True
        }
        
    elif current_status == 'OUT' and guest_info is not None:
        # Guest was found but is currently timed OUT - Process TIME IN with existing info
        print(f"\n✅ Found previous guest (currently timed out): {guest_info['name']}")
        print(f"🚗 Plate: {guest_info['plate_number']}")
        print(f"📅 Last activity: {guest_info['last_date']} at {guest_info['last_time']} (TIME OUT)")
        print(f"🎯 Match confidence: {guest_info['similarity_score']*100:.1f}%")
        print("\n🟢 PROCESSING TIME IN FOR RETURNING GUEST...")
        
        # Get the updated office information from the GUI
        updated_guest_info = updated_guest_office_gui(guest_info['name'], guest_info.get('office', 'CSS Office'))
        
        if not updated_guest_info:
            print("❌ Guest office update cancelled.")
            input("\n📱 Press Enter to return to main menu...")
            return
        
        # Process the time-in with the updated office
        existing_guest_info = {
            'name': updated_guest_info['name'],
            'plate_number': guest_info['plate_number'],
            'office': updated_guest_info['office']  # Updated office
        }
        
        # Process license verification and time in
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
        
        license_result = licenseReadGuest(image_path, guest_data_for_license)
        time_result = process_guest_time_in(existing_guest_info, license_result)
        print(f"\n🕒 {time_result['message']}")
        
        # Create verification data and results
        verification_checks = {
            '🪖 Helmet': (True, 'VERIFIED'),
            '🆔 License Detection': (True, 'VERIFIED'),
            '👤 Returning Guest': (True, f"RECOGNIZED ({guest_info['similarity_score']*100:.1f}%)")
        }
        
        gui_message = f"""
RETURNING GUEST TIME IN COMPLETE!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Guest: {existing_guest_info['name']}
🚗 Plate: {existing_guest_info['plate_number']}
🔄 Status: Returning Guest
🏢 Office: {existing_guest_info['office']}
📄 License: ✅ Verified
🎯 Recognition: {guest_info['similarity_score']*100:.1f}%

{time_result['message']}
Status: {time_result['status']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        guest_data = guest_data_for_license
        
    else:
        # New guest - not found in system - Process TIME IN
        print("\n🟢 New guest detected. Processing TIME IN...")
        
        # Get guest information through GUI
        guest_info_input = get_guest_info_gui(detected_name)
        
        if not guest_info_input:
            print("❌ Guest information cancelled.")
            input("\n📱 Press Enter to return to main menu...")
            return
        
        print(f"✅ Guest info collected:")
        print(f"   👤 Name: {guest_info_input['name']}")
        print(f"   🚗 Plate: {guest_info_input['plate_number']}")
        print(f"   🏢 Office: {guest_info_input['office']}")
        
        # Process license verification
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
        
        license_result = licenseReadGuest(image_path, guest_data_for_license)
        
        # Process time in
        time_result = process_guest_time_in(guest_info_input, license_result)
        print(f"\n🕒 {time_result['message']}")
        
        # Create verification data
        license_verified = "Driver's License Detected" in license_result.document_verified
        
        verification_checks = {
            '🪖 Helmet': (True, 'VERIFIED'),
            '🆔 License Detection': (license_verified, 'VERIFIED' if license_verified else 'PROCESSED'),
            '👤 Guest Info': (True, 'CONFIRMED')
        }
        
        gui_message = f"""
NEW GUEST TIME IN COMPLETE!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Guest: {guest_info_input['name']}
🚗 Plate: {guest_info_input['plate_number']}
🏢 Visiting: {guest_info_input['office']}
📄 License: {'✅ Verified' if license_verified else '✅ Processed'}

{time_result['message']}
Status: {time_result['status']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        guest_data = guest_data_for_license
    
    # Display results
    verification_data = {
        'checks': verification_checks,
        'overall_status': time_result['status'],
        'status_color': time_result['color'],
        'gui_message': gui_message
    }
    
    display_verification_result(guest_data, verification_data)
    input("\n📱 Press Enter to return to main menu...")

def extract_guest_name_from_license(ocr_lines):
    """Extract guest name from license OCR with improved accuracy"""
    filter_keywords = [
        'ROAD', 'STREET', 'AVENUE', 'BOULEVARD', 'DISTRICT', 'CITY', 'PROVINCE',
        'BARANGAY', 'SUBDIVISION', 'VILLAGE', 'TOWN', 'MUNICIPALITY', 'REGION',
        'REPUBLIC', 'PHILIPPINES', 'DEPARTMENT', 'TRANSPORTATION', 
        'LAND TRANSPORTATION OFFICE', 'DRIVER', 'LICENSE', 'NON-PROFESSIONAL',
        'PROFESSIONAL', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'NATIONALITY',
        'DATE', 'BIRTH', 'ADDRESS', 'WEIGHT', 'HEIGHT', 'EYES', 'HAIR', 'SEX'
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
            if 2 <= word_count <= 4: score += 5  # Reasonable name length
            if 10 <= len(line_clean) <= 30: score += 3  # Good character count
            potential_names.append((line_clean, score))
    
    # Return best match or fallback
    if potential_names:
        potential_names.sort(key=lambda x: x[1], reverse=True)
        return potential_names[0][0]
    
    return "Guest"


def find_timed_in_guest(detected_name):
    """Find a currently timed-in guest by name matching - SIMPLIFIED"""
    try:
        import sqlite3
        from difflib import SequenceMatcher
        
        conn = sqlite3.connect("database/time_tracking.db")
        cursor = conn.cursor()
        
        # Get all currently timed-in guests (status = 'IN')
        cursor.execute("""
            SELECT student_name, student_id, date, time 
            FROM time_records 
            WHERE status = 'IN' AND student_id LIKE 'GUEST_%'
            ORDER BY date DESC, time DESC
        """)
        
        timed_in_guests = cursor.fetchall()
        conn.close()
        
        if not timed_in_guests:
            return None
        
        print(f"🔍 Checking {len(timed_in_guests)} timed-in guests...")
        
        # Find best name match
        best_match = None
        highest_similarity = 0.0
        
        for guest_record in timed_in_guests:
            guest_name = guest_record[0]
            
            # Calculate similarity
            similarity = SequenceMatcher(None, detected_name.upper(), guest_name.upper()).ratio()
            
            # Boost for substring matches
            if (detected_name.upper() in guest_name.upper() or 
                guest_name.upper() in detected_name.upper()):
                similarity = max(similarity, 0.8)
            
            print(f"   📋 Comparing: '{detected_name}' vs '{guest_name}' = {similarity:.2f}")
            
            if similarity > highest_similarity and similarity > 0.6:  # 60% threshold
                highest_similarity = similarity
                best_match = guest_record
        
        if best_match:
            # Extract plate number from student_id (GUEST_PLATENUM format)
            plate_number = best_match[1].replace('GUEST_', '')
            
            return {
                'name': best_match[0],
                'student_id': best_match[1],
                'plate_number': plate_number,
                'office': 'Previous Visit',  # Simplified since we don't store office
                'time_in_date': best_match[2],
                'time_in_time': best_match[3],
                'similarity_score': highest_similarity
            }
        
        return None
        
    except Exception as e:
        print(f"❌ Error finding timed-in guest: {e}")
        return None
        
def get_guest_time_status(detected_name, plate_number=None):
    """
    Get the current time status of a guest based on name matching
    Returns: ('IN', guest_info) if currently timed in, ('OUT', guest_info) if found but timed out, (None, None) if not found
    """
    try:
        import sqlite3
        from difflib import SequenceMatcher
        
        conn = sqlite3.connect("database/time_tracking.db")
        cursor = conn.cursor()
        
        # Get the latest record for each guest to determine current status
        cursor.execute("""
            SELECT student_name, student_id, status, date, time,
                   ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY date DESC, time DESC) as row_num
            FROM time_records 
            WHERE student_id LIKE 'GUEST_%'
        """)
        
        all_records = cursor.fetchall()
        conn.close()
        
        # Filter to get only the latest record for each guest
        latest_records = [record for record in all_records if record[5] == 1]  # row_num = 1
        
        if not latest_records:
            return None, None
        
        print(f"🔍 Checking {len(latest_records)} guest records for name match...")
        
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
            
            # Additional boost for plate number match if provided
            if plate_number:
                guest_plate = record[1].replace('GUEST_', '')
                if plate_number.upper() == guest_plate.upper():
                    similarity = max(similarity, 0.9)
            
            print(f"   📋 Comparing: '{detected_name}' vs '{guest_name}' = {similarity:.2f}")
            
            if similarity > highest_similarity and similarity > 0.6:  # 60% threshold
                highest_similarity = similarity
                best_match = record
        
        if best_match:
            guest_info = {
                'name': best_match[0],
                'student_id': best_match[1],
                'plate_number': best_match[1].replace('GUEST_', ''),
                'office': 'Previous Visit',
                'current_status': best_match[2],  # 'IN' or 'OUT'
                'last_date': best_match[3],
                'last_time': best_match[4],
                'similarity_score': highest_similarity
            }
            
            return best_match[2], guest_info  # Return status and guest info
        
        return None, None
        
    except Exception as e:
        print(f"❌ Error checking guest status: {e}")
        return None, None


def create_guest_time_data(guest_info):
    """Create standardized guest data for time tracking"""
    return {
        'name': guest_info['name'],
        'student_id': f"GUEST_{guest_info['plate_number']}",
        'course': f"Guest - {guest_info['office']}",  # This is only used for time_tracking, not for queries
        'license_number': guest_info['plate_number'],
        'confidence': 100
    }

def process_guest_time_in(guest_info, license_result):
    """Process guest time in with license verification"""
    guest_time_data = create_guest_time_data(guest_info)
    
    # Check license verification
    license_verified = ("Driver's License Detected" in license_result.document_verified or 
                       "Document Detected" in license_result.document_verified)
    
    if license_verified:
        if record_time_in(guest_time_data):
            return {
                'success': True,
                'status': "✅ GUEST TIME IN SUCCESSFUL",
                'message': f"🟢 TIME IN recorded at {time.strftime('%H:%M:%S')}",
                'color': "🟢"
            }
        else:
            return {
                'success': False,
                'status': "❌ TIME IN FAILED",
                'message': "❌ Failed to record TIME IN",
                'color': "🔴"
            }
    else:
        return {
            'success': False,
            'status': "❌ VERIFICATION FAILED",
            'message': "❌ License verification failed",
            'color': "🔴"
        }

def process_guest_time_out(guest_info):
    """Process guest time out"""
    guest_time_data = create_guest_time_data(guest_info)
    
    if record_time_out(guest_time_data):
        return {
            'success': True,
            'status': "✅ GUEST TIME OUT SUCCESSFUL",
            'message': f"🔴 TIME OUT recorded at {time.strftime('%H:%M:%S')}",
            'color': "🟢"
        }
    else:
        return {
            'success': False,
            'status': "❌ TIME OUT FAILED",
            'message': "❌ Failed to record TIME OUT",
            'color': "🔴"
        }
