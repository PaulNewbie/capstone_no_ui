# database/db_operations.py - Centralized Database Operations

import sqlite3
import os
import time
from datetime import datetime

# Database file paths
STUDENT_DB_FILE = "database/students.db"
TIME_TRACKING_DB = "database/time_tracking.db"
GUEST_DB_FILE = "database/guest_info.db"  # Legacy - to be removed

# =================== DATABASE INITIALIZATION ===================

def init_time_database():
    """Initialize time tracking database"""
    try:
        os.makedirs("database", exist_ok=True)
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                student_name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS current_status (
                student_id TEXT PRIMARY KEY,
                student_name TEXT NOT NULL,
                current_status TEXT NOT NULL,
                last_update DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_records_student_id ON time_records(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_records_status ON time_records(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_current_status_status ON current_status(current_status)')
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Time database initialization error: {e}")
        return False

def init_student_database():
    """Initialize student database"""
    try:
        os.makedirs("database", exist_ok=True)
        conn = sqlite3.connect(STUDENT_DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                license_number TEXT,
                expiration_date TEXT,
                course TEXT,
                student_id TEXT UNIQUE,
                synced_at TEXT
            )
        ''')
        
        # Create index for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id)')
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Student database initialization error: {e}")
        return False

def init_guest_database():
    """Initialize clean guest database structure"""
    try:
        # Only use time_tracking.db for all guest operations
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        # Ensure tables exist with correct schema (same as time tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                student_name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS current_status (
                student_id TEXT PRIMARY KEY,
                student_name TEXT NOT NULL,
                current_status TEXT NOT NULL,
                last_update DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_records_student_id ON time_records(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_records_status ON time_records(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_current_status_status ON current_status(current_status)')
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize guest database: {e}")
        return False

def cleanup_guest_data():
    """Clean up any orphaned guest data"""
    try:
        # Remove old guest_info.db if it exists
        if os.path.exists(GUEST_DB_FILE):
            os.remove(GUEST_DB_FILE)
            print("✅ Removed old guest_info.db")
        
        # Clean up any malformed guest records in time_tracking.db
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        # Remove any guest records with invalid student_id format
        cursor.execute("DELETE FROM time_records WHERE student_id LIKE 'GUEST_%' AND LENGTH(student_id) < 7")
        cursor.execute("DELETE FROM current_status WHERE student_id LIKE 'GUEST_%' AND LENGTH(student_id) < 7")
        
        conn.commit()
        conn.close()
        
        print("✅ Guest data cleanup completed")
        return True
        
    except Exception as e:
        print(f"⚠️ Guest data cleanup warning: {e}")
        return False

# =================== STUDENT DATABASE OPERATIONS ===================

def get_student_by_id(student_id):
    """Fetch student info by ID"""
    try:
        conn = sqlite3.connect(STUDENT_DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT full_name, license_number, expiration_date, course, student_id 
            FROM students 
            WHERE student_id = ?
        ''', (student_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'full_name': result[0],
                'license_number': result[1],
                'expiration_date': result[2],
                'course': result[3],
                'student_id': result[4]
            }
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching student: {e}")
        return None

# =================== TIME TRACKING OPERATIONS ===================

def get_student_time_status(student_id):
    """Get current time status (IN/OUT)"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT current_status FROM current_status WHERE student_id = ?', (student_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 'OUT'
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching time status: {e}")
        return 'OUT'

def record_time_in(student_info):
    """Record student time in"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        current_date = time.strftime('%Y-%m-%d')
        current_time = time.strftime('%H:%M:%S')
        
        cursor.execute('''
            INSERT INTO time_records (student_id, student_name, date, time, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_info['student_id'], student_info['name'], current_date, current_time, 'IN'))
        
        cursor.execute('''
            INSERT OR REPLACE INTO current_status (student_id, student_name, current_status)
            VALUES (?, ?, ?)
        ''', (student_info['student_id'], student_info['name'], 'IN'))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error recording time in: {e}")
        return False

def record_time_out(student_info):
    """Record student time out"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        current_date = time.strftime('%Y-%m-%d')
        current_time = time.strftime('%H:%M:%S')
        
        cursor.execute('''
            INSERT INTO time_records (student_id, student_name, date, time, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_info['student_id'], student_info['name'], current_date, current_time, 'OUT'))
        
        cursor.execute('''
            INSERT OR REPLACE INTO current_status (student_id, student_name, current_status)
            VALUES (?, ?, ?)
        ''', (student_info['student_id'], student_info['name'], 'OUT'))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error recording time out: {e}")
        return False

def record_time_attendance(student_info):
    """Auto record time attendance based on current status"""
    current_status = get_student_time_status(student_info['student_id'])
    
    if current_status == 'OUT' or current_status is None:
        if record_time_in(student_info):
            return f"🟢 TIME IN recorded for {student_info['name']} at {time.strftime('%H:%M:%S')}"
        else:
            return "❌ Failed to record TIME IN"
    else:
        if record_time_out(student_info):
            return f"🔴 TIME OUT recorded for {student_info['name']} at {time.strftime('%H:%M:%S')}"
        else:
            return "❌ Failed to record TIME OUT"

def get_all_time_records():
    """Get all time records"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, student_name, date, time, status, timestamp
            FROM time_records
            ORDER BY timestamp DESC
        ''')
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'student_id': row[0],
                'student_name': row[1],
                'date': row[2],
                'time': row[3],
                'status': row[4],
                'timestamp': row[5]
            })
        
        conn.close()
        return records
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching time records: {e}")
        return []

def clear_all_time_records():
    """Clear all time records"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM time_records')
        cursor.execute('DELETE FROM current_status')
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error clearing time records: {e}")
        return False

def get_students_currently_in():
    """Get students currently timed in"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, student_name, last_update
            FROM current_status
            WHERE current_status = 'IN'
            ORDER BY last_update DESC
        ''')
        
        students = []
        for row in cursor.fetchall():
            students.append({
                'student_id': row[0],
                'student_name': row[1],
                'time_in': row[2]
            })
        
        conn.close()
        return students
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching students currently in: {e}")
        return []

# =================== SYSTEM MAINTENANCE ===================

def initialize_all_databases():
    """Initialize all system databases"""
    print("🗄️ Initializing databases...")
    
    time_db_ok = init_time_database()
    student_db_ok = init_student_database()
    guest_db_ok = init_guest_database()
    cleanup_ok = cleanup_guest_data()
    
    print(f"🗄️ Time Database: {'✅' if time_db_ok else '❌'}")
    print(f"🗄️ Student Database: {'✅' if student_db_ok else '❌'}")
    print(f"🗄️ Guest Database: {'✅' if guest_db_ok else '❌'}")
    print(f"🧹 Guest Cleanup: {'✅' if cleanup_ok else '⚠️'}")
    
    return all([time_db_ok, student_db_ok, guest_db_ok])

def get_database_stats():
    """Get database statistics"""
    try:
        stats = {}
        
        # Time records stats
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM time_records')
        stats['total_time_records'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM current_status WHERE current_status = 'IN'")
        stats['students_currently_in'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT student_id) FROM time_records WHERE student_id NOT LIKE 'GUEST_%'")
        stats['unique_students'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT student_id) FROM time_records WHERE student_id LIKE 'GUEST_%'")
        stats['unique_guests'] = cursor.fetchone()[0]
        
        conn.close()
        
        # Student database stats
        conn = sqlite3.connect(STUDENT_DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM students')
        stats['total_students_registered'] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats
        
    except sqlite3.Error as e:
        print(f"❌ Error getting database stats: {e}")
        return {}

def backup_databases(backup_dir="backups"):
    """Create backup of all databases"""
    try:
        import shutil
        from datetime import datetime
        
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backed_up = []
        
        # Backup time tracking database
        if os.path.exists(TIME_TRACKING_DB):
            backup_path = os.path.join(backup_dir, f"time_tracking_{timestamp}.db")
            shutil.copy2(TIME_TRACKING_DB, backup_path)
            backed_up.append("time_tracking.db")
        
        # Backup student database
        if os.path.exists(STUDENT_DB_FILE):
            backup_path = os.path.join(backup_dir, f"students_{timestamp}.db")
            shutil.copy2(STUDENT_DB_FILE, backup_path)
            backed_up.append("students.db")
        
        print(f"✅ Backed up databases: {', '.join(backed_up)}")
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False
