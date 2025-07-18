# database/db_operations.py - Organized Database Operations for MotorPass

import sqlite3
import os
import time
import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from database.init_database import MOTORPASS_DB, initialize_all_databases, get_database_stats

# =================== STUDENT OPERATIONS ===================

def add_student(student_data: Dict) -> bool:
    """Add or update a student record"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO students 
            (student_id, full_name, course, license_number, 
             license_expiration, plate_number, fingerprint_slot, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            student_data['student_id'],
            student_data['full_name'],
            student_data.get('course', ''),
            student_data.get('license_number'),
            student_data.get('license_expiration'),
            student_data.get('plate_number'),
            student_data.get('fingerprint_slot')
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error adding student: {e}")
        return False

def get_student_by_id(student_id: str) -> Optional[Dict]:
    """Get student by ID"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, full_name, course, license_number, 
                   license_expiration, plate_number, fingerprint_slot
            FROM students WHERE student_id = ?
        ''', (student_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'student_id': row[0],
                'full_name': row[1],
                'course': row[2],
                'license_number': row[3],
                'expiration_date': row[4],
                'plate_number': row[5],
                'fingerprint_slot': row[6],
                'user_type': 'STUDENT',
                'unified_id': row[0]
            }
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching student: {e}")
        return None

def get_all_students() -> List[Dict]:
    """Get all students"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, full_name, course, license_number, 
                   license_expiration, plate_number, fingerprint_slot
            FROM students ORDER BY full_name
        ''')
        
        students = []
        for row in cursor.fetchall():
            students.append({
                'student_id': row[0],
                'full_name': row[1],
                'course': row[2],
                'license_number': row[3],
                'license_expiration': row[4],
                'plate_number': row[5],
                'fingerprint_slot': row[6]
            })
        
        conn.close()
        return students
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching students: {e}")
        return []

# =================== STAFF OPERATIONS ===================

def add_staff(staff_data: Dict) -> bool:
    """Add or update a staff record"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO staff 
            (staff_no, full_name, staff_role, license_number, 
             license_expiration, plate_number, fingerprint_slot, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            staff_data['staff_no'],
            staff_data['full_name'],
            staff_data.get('staff_role', ''),
            staff_data.get('license_number'),
            staff_data.get('license_expiration'),
            staff_data.get('plate_number'),
            staff_data.get('fingerprint_slot')
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error adding staff: {e}")
        return False

def get_staff_by_id(staff_no: str) -> Optional[Dict]:
    """Get staff by ID"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT staff_no, full_name, staff_role, license_number, 
                   license_expiration, plate_number, fingerprint_slot
            FROM staff WHERE staff_no = ?
        ''', (staff_no,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'staff_no': row[0],
                'full_name': row[1],
                'staff_role': row[2],
                'license_number': row[3],
                'expiration_date': row[4],
                'plate_number': row[5],
                'fingerprint_slot': row[6],
                'user_type': 'STAFF',
                'unified_id': row[0]
            }
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching staff: {e}")
        return None

def get_all_staff() -> List[Dict]:
    """Get all staff members"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT staff_no, full_name, staff_role, license_number, 
                   license_expiration, plate_number, fingerprint_slot
            FROM staff ORDER BY full_name
        ''')
        
        staff_list = []
        for row in cursor.fetchall():
            staff_list.append({
                'staff_no': row[0],
                'full_name': row[1],
                'staff_role': row[2],
                'license_number': row[3],
                'license_expiration': row[4],
                'plate_number': row[5],
                'fingerprint_slot': row[6]
            })
        
        conn.close()
        return staff_list
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching staff: {e}")
        return []

# =================== GUEST OPERATIONS ===================

def add_guest(guest_data: Dict) -> str:
    """Add or update a guest record and return plate_number (guest number)"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        # Check if guest already exists by plate number
        cursor.execute('''
            SELECT guest_id FROM guests 
            WHERE plate_number = ?
        ''', (guest_data['plate_number'],))
        
        existing_guest = cursor.fetchone()
        
        if existing_guest:
            # Update existing guest
            cursor.execute('''
                UPDATE guests 
                SET full_name = ?, office_visiting = ?
                WHERE plate_number = ?
            ''', (guest_data['full_name'], guest_data['office_visiting'], guest_data['plate_number']))
        else:
            # Insert new guest
            cursor.execute('''
                INSERT INTO guests (full_name, plate_number, office_visiting)
                VALUES (?, ?, ?)
            ''', (
                guest_data['full_name'],
                guest_data['plate_number'],
                guest_data['office_visiting']
            ))
        
        conn.commit()
        conn.close()
        return guest_data['plate_number']
        
    except sqlite3.Error as e:
        print(f"❌ Error adding guest: {e}")
        return ""

def get_guest_by_plate(plate_number: str) -> Optional[Dict]:
    """Get guest by plate number"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT guest_id, full_name, plate_number, office_visiting, created_date
            FROM guests 
            WHERE plate_number = ?
            ORDER BY created_date DESC
            LIMIT 1
        ''', (plate_number,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'guest_id': row[0],
                'full_name': row[1],
                'plate_number': row[2],
                'office_visiting': row[3],
                'created_date': row[4]
            }
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching guest: {e}")
        return None

def get_guest_by_name_and_plate(name: str, plate_number: str) -> Optional[Dict]:
    """Get guest by name and plate number"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT guest_id, full_name, plate_number, office_visiting, created_date
            FROM guests 
            WHERE full_name = ? AND plate_number = ?
            ORDER BY created_date DESC
            LIMIT 1
        ''', (name, plate_number))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'guest_id': row[0],
                'full_name': row[1],
                'plate_number': row[2],
                'office_visiting': row[3],
                'created_date': row[4]
            }
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching guest: {e}")
        return None

def get_all_guests() -> List[Dict]:
    """Get all guests ordered by creation date"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT guest_id, full_name, plate_number, office_visiting, created_date
            FROM guests 
            ORDER BY created_date DESC
        ''')
        
        guests = []
        for row in cursor.fetchall():
            guests.append({
                'guest_id': row[0],
                'full_name': row[1],
                'plate_number': row[2],
                'office_visiting': row[3],
                'created_date': row[4]
            })
        
        conn.close()
        return guests
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching guests: {e}")
        return []

def search_guests(search_term: str) -> List[Dict]:
    """Search guests by name or plate number"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        search_pattern = f"%{search_term}%"
        cursor.execute('''
            SELECT guest_id, full_name, plate_number, office_visiting, created_date
            FROM guests 
            WHERE full_name LIKE ? OR plate_number LIKE ?
            ORDER BY created_date DESC
        ''', (search_pattern, search_pattern))
        
        guests = []
        for row in cursor.fetchall():
            guests.append({
                'guest_id': row[0],
                'full_name': row[1],
                'plate_number': row[2],
                'office_visiting': row[3],
                'created_date': row[4]
            })
        
        conn.close()
        return guests
        
    except sqlite3.Error as e:
        print(f"❌ Error searching guests: {e}")
        return []
        
# ==================== OTHERS for GUEST =====================

def get_guest_time_status(detected_name, plate_number=None):
    """Get current time status of guest - FIXED to only check guests currently IN"""
    try:
        import sqlite3
        from difflib import SequenceMatcher
        
        # Use the new centralized database
        conn = sqlite3.connect(MOTORPASS_DB)
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
        
        # Filter to latest records only, AND only those currently IN
        latest_records = [record for record in all_records 
                         if record[5] == 1 and record[2] == 'IN']  # row_num == 1 and action == 'IN'
        
        if not latest_records:
            return None, None
        
        print(f"🔍 Checking against {len(latest_records)} guests currently IN...")
        
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
                'current_status': best_match[2],  # action (should always be 'IN' now)
                'last_date': best_match[3],
                'last_time': best_match[4],
                'similarity_score': highest_similarity
            }
            
            return best_match[2], guest_info  # action ('IN'), guest_info
        
        return None, None
        
    except Exception as e:
        print(f"❌ Error checking guest status: {e}")
        return None, None
        
def get_guest_from_database(plate_number=None, name=None):
    """Retrieve guest information from guests table - updated without last_visit"""
    try:
        #from database.db_operations import get_guest_by_plate, get_guest_by_name_and_plate
        
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
                'created_date': guest_data['created_date']
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
        #from database.db_operations import record_time_in
        
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
            
    except Exception as e:
        print(f"❌ Error processing TIME IN: {e}")
        return {
            'success': False,
            'status': "❌ TIME IN ERROR",
            'message': f"❌ Error: {e}",
            'color': "🔴"
        }

def process_guest_time_out(guest_info):
    """Process guest time out - using new database functions"""
    try:
        #from database.db_operations import record_time_out
        
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
            
    except Exception as e:
        print(f"❌ Error processing TIME OUT: {e}")
        return {
            'success': False,
            'status': "❌ TIME OUT ERROR",
            'message': f"❌ Error: {e}",
            'color': "🔴"
        }

# =================== UNIFIED USER LOOKUP ===================

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user info by ID (works for students, staff, and guests)"""
    # Try student first
    student = get_student_by_id(user_id)
    if student:
        return student
    
    # Try staff
    staff = get_staff_by_id(user_id)
    if staff:
        return staff
    
    # Try guest (for GUEST_ prefixed IDs)
    if user_id.startswith('GUEST_'):
        plate_number = user_id.replace('GUEST_', '')
        guest = get_guest_by_plate(plate_number)
        if guest:
            return {
                'guest_id': guest['guest_id'],
                'full_name': guest['full_name'],
                'plate_number': guest['plate_number'],
                'office_visiting': guest['office_visiting'],
                'user_type': 'GUEST',
                'unified_id': user_id,
                'license_number': None,
                'expiration_date': None
            }
    
    return None

def search_all_users(search_term: str) -> List[Dict]:
    """Search across all user types"""
    results = []
    
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        search_pattern = f"%{search_term}%"
        
        # Search students
        cursor.execute('''
            SELECT student_id, full_name, course, 'STUDENT' as user_type 
            FROM students 
            WHERE student_id LIKE ? OR full_name LIKE ?
        ''', (search_pattern, search_pattern))
        
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'name': row[1],
                'details': row[2],
                'user_type': row[3]
            })
        
        # Search staff
        cursor.execute('''
            SELECT staff_no, full_name, staff_role, 'STAFF' as user_type 
            FROM staff 
            WHERE staff_no LIKE ? OR full_name LIKE ?
        ''', (search_pattern, search_pattern))
        
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'name': row[1],
                'details': row[2],
                'user_type': row[3]
            })
        
        # Search guests
        cursor.execute('''
            SELECT plate_number, full_name, office_visiting, 'GUEST' as user_type 
            FROM guests 
            WHERE plate_number LIKE ? OR full_name LIKE ?
        ''', (search_pattern, search_pattern))
        
        for row in cursor.fetchall():
            results.append({
                'id': f"GUEST_{row[0]}",
                'name': row[1],
                'details': row[2],
                'user_type': row[3]
            })
        
        conn.close()
        return results
        
    except sqlite3.Error as e:
        print(f"❌ Error searching users: {e}")
        return []

# =================== TIME TRACKING OPERATIONS ===================

def get_student_time_status(user_id: str) -> Optional[str]:
    """Get current time status for any user"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT status FROM current_status WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 'OUT'
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching status: {e}")
        return 'OUT'

def record_time_in(user_info: Dict) -> bool:
    """Record TIME IN for any user"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        user_id = user_info.get('unified_id', user_info.get('student_id', ''))
        user_name = user_info.get('name', user_info.get('full_name', ''))
        user_type = user_info.get('user_type', 'STUDENT')
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Record in time_tracking
        cursor.execute('''
            INSERT INTO time_tracking (user_id, user_name, user_type, action, date, time)
            VALUES (?, ?, ?, 'IN', ?, ?)
        ''', (user_id, user_name, user_type, current_date, current_time))
        
        # Update current_status
        cursor.execute('''
            INSERT OR REPLACE INTO current_status (user_id, user_name, user_type, status)
            VALUES (?, ?, ?, 'IN')
        ''', (user_id, user_name, user_type))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error recording time in: {e}")
        return False

def record_time_out(user_info: Dict) -> bool:
    """Record TIME OUT for any user"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        user_id = user_info.get('unified_id', user_info.get('student_id', ''))
        user_name = user_info.get('name', user_info.get('full_name', ''))
        user_type = user_info.get('user_type', 'GUEST')
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Record in time_tracking
        cursor.execute('''
            INSERT INTO time_tracking (user_id, user_name, user_type, action, date, time)
            VALUES (?, ?, ?, 'OUT', ?, ?)
        ''', (user_id, user_name, user_type, current_date, current_time))
        
        # Update current_status
        cursor.execute('''
            INSERT OR REPLACE INTO current_status (user_id, user_name, user_type, status)
            VALUES (?, ?, ?, 'OUT')
        ''', (user_id, user_name, user_type))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error recording time out: {e}")
        return False

def record_time_attendance(user_info: Dict) -> str:
    """Auto record time attendance based on current status"""
    user_id = user_info.get('unified_id', user_info.get('student_id', ''))
    current_status = get_student_time_status(user_id)
    
    if current_status == 'OUT' or current_status is None:
        if record_time_in(user_info):
            return f"🟢 TIME IN recorded for {user_info['name']} at {time.strftime('%H:%M:%S')}"
        else:
            return "❌ Failed to record TIME IN"
    else:
        if record_time_out(user_info):
            return f"🔴 TIME OUT recorded for {user_info['name']} at {time.strftime('%H:%M:%S')}"
        else:
            return "❌ Failed to record TIME OUT"

def get_all_time_records() -> List[Dict]:
    """Get all time records"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, user_name, user_type, date, time, action, timestamp
            FROM time_tracking
            ORDER BY timestamp DESC
        ''')
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'student_id': row[0],
                'student_name': row[1],
                'user_type': row[2],
                'date': row[3],
                'time': row[4],
                'status': row[5],
                'timestamp': row[6]
            })
        
        conn.close()
        return records
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching time records: {e}")
        return []

def get_students_currently_in() -> List[Dict]:
    """Get all users currently inside"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, user_name, user_type, last_action_time
            FROM current_status
            WHERE status = 'IN'
            ORDER BY last_action_time DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'student_id': row[0],
                'student_name': row[1],
                'user_type': row[2],
                'time_in': row[3]
            })
        
        conn.close()
        return users
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching users inside: {e}")
        return []

def clear_all_time_records() -> bool:
    """Clear all time tracking records"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM time_tracking')
        cursor.execute('DELETE FROM current_status')
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error clearing time records: {e}")
        return False

# =================== LEGACY COMPATIBILITY ===================

def init_student_database():
    """Legacy compatibility"""
    return initialize_all_databases()

def init_time_database():
    """Legacy compatibility"""
    return initialize_all_databases()

def get_time_records_by_date(date: str) -> List[Dict]:
    """Get time records for a specific date"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, user_name, user_type, date, time, action
            FROM time_tracking
            WHERE date = ?
            ORDER BY time DESC
        ''', (date,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'user_id': row[0],
                'user_name': row[1],
                'user_type': row[2],
                'date': row[3],
                'time': row[4],
                'action': row[5]
            })
        
        conn.close()
        return records
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching records by date: {e}")
        return []
        
# =================== SECURITY FUNCTIONS ===================

def _hash_password(password: str, salt: str) -> str:
    """Hash password with salt using SHA-256"""
    return hashlib.sha256((password + salt).encode()).hexdigest()

def _generate_salt() -> str:
    """Generate a random salt for password hashing"""
    return secrets.token_hex(32)

def _verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify password against hash"""
    return _hash_password(password, salt) == password_hash

# =================== INITIALIZATION ON IMPORT ===================

# Auto-initialize database on import
if __name__ != "__main__":
    # Only run when imported, not when run directly
    if not os.path.exists(MOTORPASS_DB):
        initialize_all_databases()
