# database/db_operations.py - Simplified version using ONLY motorpass.db

import sqlite3
import os
import time
from datetime import datetime
from typing import Optional, Dict, List

# Single database file
MOTORPASS_DB = "database/motorpass.db"

# =================== DATABASE INITIALIZATION ===================

def initialize_all_databases():
    """Initialize the centralized motorpass database"""
    try:
        os.makedirs("database", exist_ok=True)
        conn = sqlite3.connect(MOTORPASS_DB)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Create all tables
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guests (
                guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                plate_number TEXT NOT NULL,
                office_visiting TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

# =================== USER LOOKUP ===================

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user info by ID (works for both students and staff)"""
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
        user_type = user_info.get('user_type', 'STUDENT')
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
        
        # Count currently inside
        cursor.execute('SELECT COUNT(*) FROM current_status WHERE status = "IN"')
        stats['users_currently_in'] = cursor.fetchone()[0]
        
        # Breakdown by type
        cursor.execute('SELECT COUNT(*) FROM current_status WHERE status = "IN" AND user_type = "STUDENT"')
        stats['students_currently_in'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM current_status WHERE status = "IN" AND user_type = "STAFF"')
        stats['staff_currently_in'] = cursor.fetchone()[0]
        
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

# =================== LEGACY COMPATIBILITY ===================

def init_student_database():
    """Legacy compatibility"""
    return initialize_all_databases()

def init_time_database():
    """Legacy compatibility"""
    return initialize_all_databases()
