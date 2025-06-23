# database/db_operations.py - Updated for Students & Staff

import sqlite3
import os
import time
from datetime import datetime

# Database file paths
STUDENT_DB_FILE = "database/students.db"
TIME_TRACKING_DB = "database/time_tracking.db"

# =================== DATABASE INITIALIZATION ===================

def init_student_database():
    """Initialize student/staff database with updated schema"""
    try:
        os.makedirs("database", exist_ok=True)
        conn = sqlite3.connect(STUDENT_DB_FILE)
        cursor = conn.cursor()
        
        # Drop old table and create new one with updated schema
        cursor.execute('DROP TABLE IF EXISTS students')
        
        cursor.execute('''
            CREATE TABLE students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                license_number TEXT,
                expiration_date TEXT,
                plate_number TEXT,
                course TEXT,
                student_id TEXT,
                staff_role TEXT,
                staff_no TEXT,
                user_type TEXT NOT NULL,
                synced_at TEXT,
                UNIQUE(student_id, staff_no)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_staff_no ON students(staff_no)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_user_type ON students(user_type)')
        
        conn.commit()
        conn.close()
        print("✅ Student/Staff database initialized with new schema")
        return True
    except sqlite3.Error as e:
        print(f"❌ Student database initialization error: {e}")
        return False

def migrate_time_database():
    """Migrate existing time_tracking database to support user_type column"""
    try:
        if not os.path.exists(TIME_TRACKING_DB):
            return True  # No existing database to migrate
        
        print("🔄 Migrating existing time database...")
        
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        # Check if user_type column already exists in time_records
        cursor.execute("PRAGMA table_info(time_records)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_type' not in columns:
            print("📋 Adding user_type column to time_records...")
            cursor.execute("ALTER TABLE time_records ADD COLUMN user_type TEXT NOT NULL DEFAULT 'STUDENT'")
        
        # Check if user_type column exists in current_status
        cursor.execute("PRAGMA table_info(current_status)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_type' not in columns:
            print("📋 Adding user_type column to current_status...")
            cursor.execute("ALTER TABLE current_status ADD COLUMN user_type TEXT NOT NULL DEFAULT 'STUDENT'")
        
        conn.commit()
        conn.close()
        
        print("✅ Time database migration completed")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def init_time_database():
    """Initialize time tracking database with migration support"""
    try:
        os.makedirs("database", exist_ok=True)
        
        # First try migration if database exists
        if os.path.exists(TIME_TRACKING_DB):
            if not migrate_time_database():
                return False
        
        # Now ensure all tables and columns exist
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                student_name TEXT NOT NULL,
                user_type TEXT NOT NULL DEFAULT 'STUDENT',
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
                user_type TEXT NOT NULL DEFAULT 'STUDENT',
                current_status TEXT NOT NULL,
                last_update DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_records_student_id ON time_records(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_records_status ON time_records(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_records_user_type ON time_records(user_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_current_status_status ON current_status(current_status)')
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Time database initialization error: {e}")
        return False

# =================== USER LOOKUP FUNCTIONS ===================

def get_user_by_id(user_id):
    """Fetch user info by Student ID or Staff No"""
    try:
        conn = sqlite3.connect(STUDENT_DB_FILE)
        cursor = conn.cursor()
        
        # Try to find by student_id first, then by staff_no
        cursor.execute('''
            SELECT full_name, license_number, expiration_date, plate_number, 
                   course, student_id, staff_role, staff_no, user_type 
            FROM students 
            WHERE student_id = ? OR staff_no = ?
        ''', (user_id, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'full_name': result[0],
                'license_number': result[1],
                'expiration_date': result[2],
                'plate_number': result[3],
                'course': result[4],
                'student_id': result[5],
                'staff_role': result[6],
                'staff_no': result[7],
                'user_type': result[8],
                # Create unified ID field for time tracking
                'unified_id': result[5] if result[8] == 'STUDENT' else result[7]
            }
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching user: {e}")
        return None

def get_student_by_id(student_id):
    """Legacy function - redirects to get_user_by_id"""
    return get_user_by_id(student_id)

# =================== TIME TRACKING OPERATIONS ===================

def get_student_time_status(user_id):
    """Get current time status (IN/OUT) for student or staff"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT current_status FROM current_status WHERE student_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 'OUT'
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching time status: {e}")
        return 'OUT'

def record_time_in(user_info):
    """Record user time in (works for both students and staff)"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        current_date = time.strftime('%Y-%m-%d')
        current_time = time.strftime('%H:%M:%S')
        
        # Use unified_id for time tracking
        user_id = user_info.get('unified_id', user_info.get('student_id', ''))
        user_type = user_info.get('user_type', 'STUDENT')
        
        cursor.execute('''
            INSERT INTO time_records (student_id, student_name, user_type, date, time, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, user_info['name'], user_type, current_date, current_time, 'IN'))
        
        cursor.execute('''
            INSERT OR REPLACE INTO current_status (student_id, student_name, user_type, current_status)
            VALUES (?, ?, ?, ?)
        ''', (user_id, user_info['name'], user_type, 'IN'))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error recording time in: {e}")
        return False

def record_time_out(user_info):
    """Record user time out (works for both students and staff)"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        current_date = time.strftime('%Y-%m-%d')
        current_time = time.strftime('%H:%M:%S')
        
        # Use unified_id for time tracking
        user_id = user_info.get('unified_id', user_info.get('student_id', ''))
        user_type = user_info.get('user_type', 'STUDENT')
        
        cursor.execute('''
            INSERT INTO time_records (student_id, student_name, user_type, date, time, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, user_info['name'], user_type, current_date, current_time, 'OUT'))
        
        cursor.execute('''
            INSERT OR REPLACE INTO current_status (student_id, student_name, user_type, current_status)
            VALUES (?, ?, ?, ?)
        ''', (user_id, user_info['name'], user_type, 'OUT'))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error recording time out: {e}")
        return False

def record_time_attendance(user_info):
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

def get_all_time_records():
    """Get all time records"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, student_name, user_type, date, time, status, timestamp
            FROM time_records
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
    """Get users currently timed in"""
    try:
        conn = sqlite3.connect(TIME_TRACKING_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, student_name, user_type, last_update
            FROM current_status
            WHERE current_status = 'IN'
            ORDER BY last_update DESC
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
        print(f"❌ Error fetching users currently in: {e}")
        return []

# =================== SYSTEM MAINTENANCE ===================

def initialize_all_databases():
    """Initialize all system databases"""
    print("🗄️ Initializing databases...")
    
    time_db_ok = init_time_database()
    student_db_ok = init_student_database()
    
    print(f"🗄️ Time Database: {'✅' if time_db_ok else '❌'}")
    print(f"🗄️ Student/Staff Database: {'✅' if student_db_ok else '❌'}")
    
    return all([time_db_ok, student_db_ok])

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
        stats['users_currently_in'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM current_status WHERE current_status = 'IN' AND user_type = 'STUDENT'")
        stats['students_currently_in'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM current_status WHERE current_status = 'IN' AND user_type = 'STAFF'")
        stats['staff_currently_in'] = cursor.fetchone()[0]
        
        conn.close()
        
        # User database stats
        conn = sqlite3.connect(STUDENT_DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM students WHERE user_type = 'STUDENT'")
        stats['total_students_registered'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM students WHERE user_type = 'STAFF'")
        stats['total_staff_registered'] = cursor.fetchone()[0]
        
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
