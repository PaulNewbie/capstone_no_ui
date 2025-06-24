# database/db_operations.py - Updated version with proper guest handling

import sqlite3
import os
import time
from datetime import datetime
from typing import Optional, Dict, List

# Single database file
MOTORPASS_DB = "database/motorpass.db"

# =================== DATABASE INITIALIZATION ===================

def initialize_all_databases():
    """Initialize the centralized motorpass database with updated schema"""
    try:
        os.makedirs("database", exist_ok=True)
        conn = sqlite3.connect(MOTORPASS_DB)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Create all tables with updated schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                course TEXT NOT NULL,
                license_number TEXT,
                license_expiration DATE,
                plate_number TEXT,
                fingerprint_slot INTEGER UNIQUE,
                enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                staff_no TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                staff_role TEXT NOT NULL,
                license_number TEXT,
                license_expiration DATE,
                plate_number TEXT,
                fingerprint_slot INTEGER UNIQUE,
                enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Updated guests table - only essential fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guests (
                guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                plate_number TEXT NOT NULL,
                office_visiting TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                user_type TEXT NOT NULL CHECK(user_type IN ('STUDENT', 'STAFF', 'GUEST')),
                action TEXT NOT NULL CHECK(action IN ('IN', 'OUT')),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date DATE NOT NULL,
                time TIME NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS current_status (
                user_id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                user_type TEXT NOT NULL CHECK(user_type IN ('STUDENT', 'STAFF', 'GUEST')),
                status TEXT NOT NULL CHECK(status IN ('IN', 'OUT')),
                last_action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_name ON students(full_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_staff_name ON staff(full_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guests_name ON guests(full_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guests_plate ON guests(plate_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_tracking_user ON time_tracking(user_id, user_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_tracking_date ON time_tracking(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_current_status_type ON current_status(user_type)')
        
        conn.commit()
        conn.close()
        
        print("✅ MotorPass database initialized successfully")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database initialization error: {e}")
        return False

# =================== GUEST OPERATIONS ===================

def add_guest(guest_data: Dict) -> str:
    """Add or update a guest record and return plate_number (guest number)"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        # Check if guest already exists by plate number (guest number)
        cursor.execute('''
            SELECT plate_number FROM guests 
            WHERE plate_number = ?
        ''', (guest_data['plate_number'],))
        
        existing_guest = cursor.fetchone()
        
        if existing_guest:
            # Update existing guest info
            cursor.execute('''
                UPDATE guests 
                SET full_name = ?, office_visiting = ?, last_visit = CURRENT_TIMESTAMP
                WHERE plate_number = ?
            ''', (guest_data['full_name'], guest_data['office_visiting'], guest_data['plate_number']))
            
            conn.commit()
            conn.close()
            print(f"✅ Updated guest: {guest_data['full_name']} (Guest No: {guest_data['plate_number']})")
            return guest_data['plate_number']
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
            print(f"✅ Added new guest: {guest_data['full_name']} (Guest No: {guest_data['plate_number']})")
            return guest_data['plate_number']
        
    except sqlite3.Error as e:
        print(f"❌ Error adding guest: {e}")
        return ""

def get_guest_by_plate(plate_number: str) -> Optional[Dict]:
    """Get guest by plate number (most recent)"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT guest_id, full_name, plate_number, office_visiting, created_date, last_visit
            FROM guests 
            WHERE plate_number = ?
            ORDER BY last_visit DESC
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
                'created_date': row[4],
                'last_visit': row[5]
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
            SELECT guest_id, full_name, plate_number, office_visiting, created_date, last_visit
            FROM guests 
            WHERE full_name = ? AND plate_number = ?
            ORDER BY last_visit DESC
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
                'created_date': row[4],
                'last_visit': row[5]
            }
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching guest: {e}")
        return None

def get_all_guests() -> List[Dict]:
    """Get all guests ordered by last visit"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT guest_id, full_name, plate_number, office_visiting, created_date, last_visit
            FROM guests 
            ORDER BY last_visit DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'guest_id': row[0],
            'full_name': row[1],
            'plate_number': row[2],
            'office_visiting': row[3],
            'created_date': row[4],
            'last_visit': row[5]
        } for row in rows]
        
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
            SELECT guest_id, full_name, plate_number, office_visiting, created_date, last_visit
            FROM guests 
            WHERE full_name LIKE ? OR plate_number LIKE ?
            ORDER BY last_visit DESC
        ''', (search_pattern, search_pattern))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'guest_id': row[0],
            'full_name': row[1],
            'plate_number': row[2],
            'office_visiting': row[3],
            'created_date': row[4],
            'last_visit': row[5]
        } for row in rows]
        
    except sqlite3.Error as e:
        print(f"❌ Error searching guests: {e}")
        return []

# =================== USER LOOKUP ===================

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user info by ID (works for students, staff, and guests)"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        # Try student first
        cursor.execute('''
            SELECT student_id, full_name, course, license_number, 
                   license_expiration, plate_number, fingerprint_slot
            FROM students WHERE student_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if row:
            conn.close()
            return {
                'student_id': row[0],
                'full_name': row[1],
                'course': row[2],
                'license_number': row[3],
                'expiration_date': row[4],
                'plate_number': row[5],
                'fingerprint_slot': row[6],
                'staff_no': None,
                'staff_role': None,
                'user_type': 'STUDENT',
                'unified_id': row[0]
            }
        
        # Try staff
        cursor.execute('''
            SELECT staff_no, full_name, staff_role, license_number, 
                   license_expiration, plate_number, fingerprint_slot
            FROM staff WHERE staff_no = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if row:
            conn.close()
            return {
                'staff_no': row[0],
                'full_name': row[1],
                'staff_role': row[2],
                'license_number': row[3],
                'expiration_date': row[4],
                'plate_number': row[5],
                'fingerprint_slot': row[6],
                'student_id': None,
                'course': None,
                'user_type': 'STAFF',
                'unified_id': row[0]
            }
        
        # Try guest (for GUEST_ prefixed IDs)
        if user_id.startswith('GUEST_'):
            plate_number = user_id.replace('GUEST_', '')
            guest = get_guest_by_plate(plate_number)
            if guest:
                conn.close()
                return {
                    'guest_id': guest['guest_id'],
                    'full_name': guest['full_name'],
                    'plate_number': guest['plate_number'],
                    'office_visiting': guest['office_visiting'],
                    'user_type': 'GUEST',
                    'unified_id': user_id,
                    # No license fields for guests
                    'license_number': None,
                    'expiration_date': None,
                    'course': None,
                    'staff_role': None
                }
        
        conn.close()
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching user: {e}")
        return None

# Legacy support
def get_student_by_id(student_id: str) -> Optional[Dict]:
    return get_user_by_id(student_id)

# =================== TIME TRACKING ===================

def get_student_time_status(user_id: str) -> Optional[str]:
    """Get current time status for a user"""
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
    """Record TIME IN for a user"""
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
    """Record TIME OUT for a user"""
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

# =================== DATABASE STATISTICS ===================

def get_database_stats() -> Dict:
    """Get database statistics"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        stats = {}
        
        # Count students
        cursor.execute('SELECT COUNT(*) FROM students')
        stats['total_students'] = stats['total_students_registered'] = cursor.fetchone()[0]
        
        # Count staff
        cursor.execute('SELECT COUNT(*) FROM staff')
        stats['total_staff'] = stats['total_staff_registered'] = cursor.fetchone()[0]
        
        # Count guests
        cursor.execute('SELECT COUNT(*) FROM guests')
        stats['total_guests'] = cursor.fetchone()[0]
        
        # Count currently inside
        cursor.execute('SELECT COUNT(*) FROM current_status WHERE status = "IN"')
        stats['users_currently_in'] = cursor.fetchone()[0]
        
        # Breakdown by type
        cursor.execute('SELECT COUNT(*) FROM current_status WHERE status = "IN" AND user_type = "STUDENT"')
        stats['students_currently_in'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM current_status WHERE status = "IN" AND user_type = "STAFF"')
        stats['staff_currently_in'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM current_status WHERE status = "IN" AND user_type = "GUEST"')
        stats['guests_currently_in'] = cursor.fetchone()[0]
        
        # Today's activity
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM time_tracking WHERE date = ?', (today,))
        stats['todays_activity'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
        
    except sqlite3.Error as e:
        print(f"❌ Error getting statistics: {e}")
        return {}

def backup_databases(backup_dir: str = "backups") -> bool:
    """Create backup of the database"""
    try:
        import shutil
        
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"motorpass_{timestamp}.db")
        
        if os.path.exists(MOTORPASS_DB):
            shutil.copy2(MOTORPASS_DB, backup_path)
            print(f"✅ Database backed up to: {backup_path}")
            return True
        else:
            print("❌ Database file not found")
            return False
            
    except Exception as e:
        print(f"❌ Backup error: {e}")
        return False

# =================== DATABASE MIGRATION ===================

def migrate_guest_table():
    """Migrate existing guests table to new schema"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        # Check if old guests table exists and has old structure
        cursor.execute("PRAGMA table_info(guests)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'last_visit' not in columns:
            print("🔄 Migrating guests table to new schema...")
            
            # Add new column
            cursor.execute('ALTER TABLE guests ADD COLUMN last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            
            # Update last_visit to created_date for existing records
            cursor.execute('UPDATE guests SET last_visit = created_date')
            
            print("✅ Guests table migration completed")
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Migration error: {e}")
        return False

# =================== LEGACY COMPATIBILITY ===================

def init_student_database():
    """Legacy compatibility"""
    return initialize_all_databases()

def init_time_database():
    """Legacy compatibility"""
    return initialize_all_databases()

# =================== INITIALIZATION WITH MIGRATION ===================

def initialize_with_migration():
    """Initialize database and run migrations"""
    success = initialize_all_databases()
    if success:
        migrate_guest_table()
    return success
