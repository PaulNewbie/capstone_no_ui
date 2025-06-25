import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Single database file
MOTORPASS_DB = "database/motorpass.db"

# =================== DATABASE INITIALIZATION ===================

def initialize_all_databases():
    """Initialize the centralized motorpass database with all tables"""
    try:
        os.makedirs("database", exist_ok=True)
        conn = sqlite3.connect(MOTORPASS_DB)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # ===== ADMIN TABLE =====
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'admin',
                fingerprint_slot INTEGER UNIQUE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # ===== STUDENTS TABLE =====
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
        
        # ===== STAFF TABLE =====
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
        
        # ===== GUESTS TABLE (without last_visit) =====
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guests (
                guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                plate_number TEXT NOT NULL,
                office_visiting TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ===== TIME TRACKING TABLE =====
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
        
        # ===== CURRENT STATUS TABLE =====
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS current_status (
                user_id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                user_type TEXT NOT NULL CHECK(user_type IN ('STUDENT', 'STAFF', 'GUEST')),
                status TEXT NOT NULL CHECK(status IN ('IN', 'OUT')),
                last_action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ===== CREATE INDEXES =====
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username)')
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


# =================== BACKUP AND MAINTENANCE ===================


def verify_database_integrity() -> bool:
    """Verify database integrity"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        # Check all tables exist
        required_tables = ['admins', 'students', 'staff', 'guests', 'time_tracking', 'current_status']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in required_tables:
            if table not in existing_tables:
                print(f"❌ Missing table: {table}")
                conn.close()
                return False
        
        # Run integrity check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        conn.close()
        
        if result == "ok":
            print("✅ Database integrity verified")
            return True
        else:
            print(f"❌ Database integrity check failed: {result}")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Error checking database integrity: {e}")
        return False
        
# =================== DATABASE STATISTICS ===================

def get_database_stats() -> Dict:
    """Get comprehensive database statistics"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        stats = {}
        
        # User counts
        cursor.execute('SELECT COUNT(*) FROM students')
        stats['total_students'] = stats['total_students_registered'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM staff')
        stats['total_staff'] = stats['total_staff_registered'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM guests')
        stats['total_guests'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM admins')
        stats['total_admins'] = cursor.fetchone()[0]
        
        # Currently inside counts
        cursor.execute('SELECT COUNT(*) FROM current_status WHERE status = "IN"')
        stats['users_currently_in'] = cursor.fetchone()[0]
        
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
        
        # Today's breakdown
        cursor.execute('''
            SELECT user_type, COUNT(*) 
            FROM time_tracking 
            WHERE date = ? 
            GROUP BY user_type
        ''', (today,))
        
        for row in cursor.fetchall():
            stats[f'todays_{row[0].lower()}_activity'] = row[1]
        
        conn.close()
        return stats
        
    except sqlite3.Error as e:
        print(f"❌ Error getting statistics: {e}")
        return {}


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
