# database/unified_db.py - Complete Database System

import sqlite3
import os
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import secrets

def get_database_path():
    """Get the correct database path regardless of where script is run from"""
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(current_file))
    db_path = os.path.join(project_root, "database", "motorpass.db")
    print(f"🗄️ Using database: {db_path}")
    return db_path

# Use dynamic path
DB_FILE = get_database_path()
DB_VERSION = "2.0"

# Security Configuration
SALT_LENGTH = 32
HASH_ITERATIONS = 100000

class MotorPassDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = get_database_path()
        
        self.db_path = db_path
        self.ensure_database_directory()
        self.initialize_database()
    
    def ensure_database_directory(self):
        """Create database directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        """Get database connection with proper settings"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # System info table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_info (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    course TEXT,
                    license_number TEXT,
                    license_expiration DATE,
                    fingerprint_slot INTEGER UNIQUE,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Admins table (secure)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    fingerprint_slot INTEGER UNIQUE,
                    last_login DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Time records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS time_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT NOT NULL,
                    person_name TEXT NOT NULL,
                    person_type TEXT NOT NULL CHECK(person_type IN ('STUDENT', 'GUEST')),
                    action TEXT NOT NULL CHECK(action IN ('IN', 'OUT')),
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    date DATE DEFAULT (DATE('now')),
                    time TIME DEFAULT (TIME('now')),
                    additional_info TEXT
                )
            ''')
            
            # Current status table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS current_status (
                    person_id TEXT PRIMARY KEY,
                    person_name TEXT NOT NULL,
                    person_type TEXT NOT NULL CHECK(person_type IN ('STUDENT', 'GUEST')),
                    current_status TEXT NOT NULL CHECK(current_status IN ('IN', 'OUT')),
                    last_action_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    additional_info TEXT
                )
            ''')
            
            # Guests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS guests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guest_id TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    plate_number TEXT NOT NULL,
                    office_visiting TEXT NOT NULL,
                    phone_number TEXT,
                    first_visit_date DATE DEFAULT (DATE('now')),
                    last_visit_date DATE DEFAULT (DATE('now')),
                    total_visits INTEGER DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id)",
                "CREATE INDEX IF NOT EXISTS idx_students_fingerprint ON students(fingerprint_slot)",
                "CREATE INDEX IF NOT EXISTS idx_time_records_person ON time_records(person_id, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_time_records_date ON time_records(date)",
                "CREATE INDEX IF NOT EXISTS idx_current_status_type ON current_status(person_type, current_status)",
                "CREATE INDEX IF NOT EXISTS idx_guests_plate ON guests(plate_number)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            # Set initial system info
            cursor.execute("INSERT OR IGNORE INTO system_info (key, value) VALUES (?, ?)", 
                         ("db_version", DB_VERSION))
            cursor.execute("INSERT OR IGNORE INTO system_info (key, value) VALUES (?, ?)", 
                         ("initialized_at", datetime.now().isoformat()))
            
            conn.commit()
            print("✅ Database initialized successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Database initialization error: {e}")
            raise
        finally:
            conn.close()
    
    # =================== SECURITY FUNCTIONS ===================
    
    def hash_password(self, password: str, salt: bytes = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_bytes(SALT_LENGTH)
        
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, HASH_ITERATIONS)
        return password_hash.hex(), salt.hex()
    
    def verify_password(self, password: str, stored_hash: str, stored_salt: str) -> bool:
        """Verify password against stored hash"""
        salt = bytes.fromhex(stored_salt)
        password_hash, _ = self.hash_password(password, salt)
        return password_hash == stored_hash
    
    # =================== STUDENT OPERATIONS ===================
    
    def add_student(self, student_id: str, full_name: str, course: str = None, 
                   license_number: str = None, license_expiration: str = None, 
                   fingerprint_slot: int = None) -> bool:
        """Add new student"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO students (student_id, full_name, course, license_number, 
                                    license_expiration, fingerprint_slot)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_id, full_name, course, license_number, license_expiration, fingerprint_slot))
            
            conn.commit()
            print(f"✅ Student added: {full_name} ({student_id})")
            return True
            
        except sqlite3.IntegrityError as e:
            if "student_id" in str(e):
                print(f"❌ Student ID {student_id} already exists")
            elif "fingerprint_slot" in str(e):
                print(f"❌ Fingerprint slot {fingerprint_slot} already in use")
            else:
                print(f"❌ Student creation error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error adding student: {e}")
            return False
        finally:
            conn.close()
    
    def get_student(self, student_id: str = None, fingerprint_slot: int = None) -> Optional[Dict]:
        """Get student by ID or fingerprint slot"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            if student_id:
                cursor.execute("SELECT * FROM students WHERE student_id = ? AND is_active = 1", (student_id,))
            elif fingerprint_slot:
                cursor.execute("SELECT * FROM students WHERE fingerprint_slot = ? AND is_active = 1", (fingerprint_slot,))
            else:
                return None
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            print(f"❌ Error fetching student: {e}")
            return None
        finally:
            conn.close()
    
    def update_student(self, student_id: str, **kwargs) -> bool:
        """Update student information"""
        if not kwargs:
            return False
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Build dynamic update query
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [student_id]
            
            cursor.execute(f'''
                UPDATE students 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
                WHERE student_id = ?
            ''', values)
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"✅ Student {student_id} updated")
                return True
            else:
                print(f"❌ Student {student_id} not found")
                return False
                
        except Exception as e:
            print(f"❌ Error updating student: {e}")
            return False
        finally:
            conn.close()
    
    def get_all_students(self, active_only: bool = True) -> List[Dict]:
        """Get all students"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute("SELECT * FROM students WHERE is_active = 1 ORDER BY full_name")
            else:
                cursor.execute("SELECT * FROM students ORDER BY full_name")
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"❌ Error fetching students: {e}")
            return []
        finally:
            conn.close()
    
    # =================== TIME TRACKING OPERATIONS ===================
    
    def record_time_action(self, person_id: str, person_name: str, person_type: str, 
                          action: str, additional_info: str = None) -> bool:
        """Record time IN/OUT action with local timezone"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Get local timestamp
            local_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            local_date = datetime.now().strftime('%Y-%m-%d')
            local_time = datetime.now().strftime('%H:%M:%S')
            
            # Insert time record with local time
            cursor.execute('''
                INSERT INTO time_records (person_id, person_name, person_type, action, 
                                        timestamp, date, time, additional_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (person_id, person_name, person_type, action, local_timestamp, 
                  local_date, local_time, additional_info))
            
            # Update current status with local time
            cursor.execute('''
                INSERT OR REPLACE INTO current_status 
                (person_id, person_name, person_type, current_status, last_action_time, additional_info)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (person_id, person_name, person_type, action, local_timestamp, additional_info))
            
            conn.commit()
            print(f"✅ Time {action} recorded: {person_name} ({person_type})")
            return True
            
        except Exception as e:
            print(f"❌ Error recording time action: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_current_status(self, person_id: str) -> Optional[str]:
        """Get current IN/OUT status"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT current_status FROM current_status WHERE person_id = ?
            ''', (person_id,))
            
            row = cursor.fetchone()
            return row['current_status'] if row else 'OUT'
            
        except Exception as e:
            print(f"❌ Error getting current status: {e}")
            return 'OUT'
        finally:
            conn.close()
    
    def get_people_currently_inside(self, person_type: str = None) -> List[Dict]:
        """Get all people currently inside"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            if person_type:
                cursor.execute('''
                    SELECT * FROM current_status 
                    WHERE current_status = 'IN' AND person_type = ?
                    ORDER BY last_action_time DESC
                ''', (person_type,))
            else:
                cursor.execute('''
                    SELECT * FROM current_status 
                    WHERE current_status = 'IN'
                    ORDER BY person_type, last_action_time DESC
                ''')
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"❌ Error getting people inside: {e}")
            return []
        finally:
            conn.close()
    
    def get_time_records(self, date_from: str = None, date_to: str = None, 
                        person_type: str = None, limit: int = 100) -> List[Dict]:
        """Get time records with filters"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            query = "SELECT * FROM time_records WHERE 1=1"
            params = []
            
            if date_from:
                query += " AND date >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND date <= ?"
                params.append(date_to)
            
            if person_type:
                query += " AND person_type = ?"
                params.append(person_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"❌ Error getting time records: {e}")
            return []
        finally:
            conn.close()
    
    # =================== GUEST OPERATIONS ===================
    
    def add_or_update_guest(self, full_name: str, plate_number: str, office_visiting: str, 
                           phone_number: str = None) -> str:
        """Add new guest or update existing one"""
        guest_id = f"GUEST_{plate_number}"
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Check if guest exists
            cursor.execute("SELECT id, total_visits FROM guests WHERE guest_id = ?", (guest_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing guest
                new_visit_count = existing['total_visits'] + 1
                cursor.execute('''
                    UPDATE guests 
                    SET full_name = ?, office_visiting = ?, phone_number = ?, 
                        last_visit_date = DATE('now'), total_visits = ?
                    WHERE guest_id = ?
                ''', (full_name, office_visiting, phone_number, new_visit_count, guest_id))
                print(f"✅ Guest updated: {full_name} (Visit #{new_visit_count})")
            else:
                # Add new guest
                cursor.execute('''
                    INSERT INTO guests (guest_id, full_name, plate_number, office_visiting, phone_number)
                    VALUES (?, ?, ?, ?, ?)
                ''', (guest_id, full_name, plate_number, office_visiting, phone_number))
                print(f"✅ New guest added: {full_name}")
            
            conn.commit()
            return guest_id
            
        except Exception as e:
            print(f"❌ Error managing guest: {e}")
            return guest_id
        finally:
            conn.close()
    
    def get_guest(self, guest_id: str = None, plate_number: str = None) -> Optional[Dict]:
        """Get guest by ID or plate number"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            if guest_id:
                cursor.execute("SELECT * FROM guests WHERE guest_id = ? AND is_active = 1", (guest_id,))
            elif plate_number:
                cursor.execute("SELECT * FROM guests WHERE plate_number = ? AND is_active = 1", (plate_number,))
            else:
                return None
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            print(f"❌ Error fetching guest: {e}")
            return None
        finally:
            conn.close()
    
    # =================== REPORT OPERATIONS ===================
    
    def generate_daily_report(self, target_date: str = None) -> Dict:
        """Generate daily report"""
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Students
            cursor.execute('''
                SELECT action, COUNT(*) as count
                FROM time_records 
                WHERE date = ? AND person_type = 'STUDENT'
                GROUP BY action
            ''', (target_date,))
            
            student_actions = {row['action']: row['count'] for row in cursor.fetchall()}
            
            # Guests
            cursor.execute('''
                SELECT action, COUNT(*) as count
                FROM time_records 
                WHERE date = ? AND person_type = 'GUEST'
                GROUP BY action
            ''', (target_date,))
            
            guest_actions = {row['action']: row['count'] for row in cursor.fetchall()}
            
            # Currently inside
            cursor.execute('''
                SELECT person_type, COUNT(*) as count
                FROM current_status 
                WHERE current_status = 'IN'
                GROUP BY person_type
            ''')
            
            currently_inside = {row['person_type']: row['count'] for row in cursor.fetchall()}
            
            return {
                'date': target_date,
                'students': {
                    'time_in': student_actions.get('IN', 0),
                    'time_out': student_actions.get('OUT', 0),
                    'currently_inside': currently_inside.get('STUDENT', 0)
                },
                'guests': {
                    'time_in': guest_actions.get('IN', 0),
                    'time_out': guest_actions.get('OUT', 0),
                    'currently_inside': currently_inside.get('GUEST', 0)
                },
                'total_currently_inside': sum(currently_inside.values()),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error generating daily report: {e}")
            return {}
        finally:
            conn.close()
    
    def get_dashboard_summary(self) -> Dict:
        """Get summary data for admin dashboard"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Today's stats
            today = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT 
                    person_type,
                    action,
                    COUNT(*) as count
                FROM time_records 
                WHERE date = ?
                GROUP BY person_type, action
            ''', (today,))
            
            today_actions = {}
            for row in cursor.fetchall():
                if row['person_type'] not in today_actions:
                    today_actions[row['person_type']] = {}
                today_actions[row['person_type']][row['action']] = row['count']
            
            # Currently inside
            cursor.execute('''
                SELECT person_type, COUNT(*) as count
                FROM current_status 
                WHERE current_status = 'IN'
                GROUP BY person_type
            ''')
            
            currently_inside = {row['person_type']: row['count'] for row in cursor.fetchall()}
            
            # Total registered
            cursor.execute("SELECT COUNT(*) as count FROM students WHERE is_active = 1")
            total_students = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM guests WHERE is_active = 1")
            total_guests = cursor.fetchone()['count']
            
            return {
                'today': today,
                'today_actions': today_actions,
                'currently_inside': currently_inside,
                'total_currently_inside': sum(currently_inside.values()),
                'total_students': total_students,
                'total_guests': total_guests,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting dashboard summary: {e}")
            return {}
        finally:
            conn.close()
    
    # =================== MAINTENANCE OPERATIONS ===================
    
    def clear_all_time_records(self) -> bool:
        """Clear all time records"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM time_records")
            cursor.execute("DELETE FROM current_status")
            
            conn.commit()
            print("✅ All time records cleared")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing time records: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count records in each table
            tables = ['students', 'time_records', 'current_status', 'guests']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[f'total_{table}'] = cursor.fetchone()['count']
            
            # Currently inside
            cursor.execute("SELECT COUNT(*) as count FROM current_status WHERE current_status = 'IN'")
            stats['currently_inside'] = cursor.fetchone()['count']
            
            # Today's activity
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) as count FROM time_records WHERE date = ?", (today,))
            stats['today_activity'] = cursor.fetchone()['count']
            
            # Database size
            stats['database_size'] = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
            return {}
        finally:
            conn.close()

# Create global instance
db = MotorPassDatabase()

# =================== COMPATIBILITY FUNCTIONS ===================

def initialize_all_databases():
    """Initialize database (compatibility function)"""
    try:
        db.initialize_database()
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def get_student_by_id(student_id: str):
    """Get student by ID (compatibility)"""
    student = db.get_student(student_id=student_id)
    if student:
        return {
            'full_name': student['full_name'],
            'license_number': student['license_number'],
            'expiration_date': student['license_expiration'],
            'course': student['course'],
            'student_id': student['student_id']
        }
    return None

def get_student_time_status(student_id: str):
    """Get student time status (compatibility)"""
    return db.get_current_status(student_id)

def record_time_in(student_info: dict):
    """Record time in (compatibility)"""
    return db.record_time_action(
        person_id=student_info['student_id'],
        person_name=student_info['name'],
        person_type='STUDENT',
        action='IN'
    )

def record_time_out(student_info: dict):
    """Record time out (compatibility)"""
    return db.record_time_action(
        person_id=student_info['student_id'],
        person_name=student_info['name'],
        person_type='STUDENT',
        action='OUT'
    )

def get_all_time_records():
    """Get all time records (compatibility)"""
    records = db.get_time_records(limit=1000)
    return [{
        'student_id': r['person_id'],
        'student_name': r['person_name'],
        'date': r['date'],
        'time': r['time'],
        'status': r['action'],
        'timestamp': r['timestamp']
    } for r in records]

def clear_all_time_records():
    """Clear all time records (compatibility)"""
    return db.clear_all_time_records()

def get_students_currently_in():
    """Get students currently in (compatibility)"""
    people = db.get_people_currently_inside('STUDENT')
    return [{
        'student_id': p['person_id'],
        'student_name': p['person_name'],
        'time_in': p['last_action_time']
    } for p in people]

def get_dashboard_summary():
    """Get dashboard summary (compatibility)"""
    return db.get_dashboard_summary()

# Print initialization message
print("🗄️ MotorPass Database System Ready")
print(f"📂 Database location: {DB_FILE}")
