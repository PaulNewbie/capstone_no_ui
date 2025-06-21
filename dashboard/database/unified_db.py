# database/unified_db.py - Unified MotorPass Database System

import sqlite3
import os
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import secrets

# Database Configuration
DB_FILE = "dashboard/database/motorpass.db"
DB_VERSION = "2.0"

# Security Configuration
SALT_LENGTH = 32
HASH_ITERATIONS = 100000

class MotorPassDatabase:
    def __init__(self, db_path: str = DB_FILE):
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
            
            # Archive table for old records
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS archived_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_table TEXT NOT NULL,
                    original_id INTEGER,
                    data TEXT NOT NULL,
                    archived_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    archived_reason TEXT
                )
            ''')
            
            # Reports table for admin dashboard
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    report_date DATE DEFAULT (DATE('now')),
                    data TEXT NOT NULL,
                    generated_by TEXT,
                    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id)",
                "CREATE INDEX IF NOT EXISTS idx_students_fingerprint ON students(fingerprint_slot)",
                "CREATE INDEX IF NOT EXISTS idx_time_records_person ON time_records(person_id, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_time_records_date ON time_records(date)",
                "CREATE INDEX IF NOT EXISTS idx_current_status_type ON current_status(person_type, current_status)",
                "CREATE INDEX IF NOT EXISTS idx_guests_plate ON guests(plate_number)",
                "CREATE INDEX IF NOT EXISTS idx_archived_table ON archived_records(original_table, archived_at)"
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
    
    def deactivate_student(self, student_id: str) -> bool:
        """Deactivate student (soft delete)"""
        return self.update_student(student_id, is_active=False)
    
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
    
    # =================== ADMIN OPERATIONS ===================
    
    def add_admin(self, username: str, password: str, full_name: str, fingerprint_slot: int = None) -> bool:
        """Add new admin with secure password"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Hash password
            password_hash, salt = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO admins (username, password_hash, salt, full_name, fingerprint_slot)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, salt, full_name, fingerprint_slot))
            
            conn.commit()
            print(f"✅ Admin added: {full_name} ({username})")
            return True
            
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                print(f"❌ Username {username} already exists")
            elif "fingerprint_slot" in str(e):
                print(f"❌ Fingerprint slot {fingerprint_slot} already in use")
            else:
                print(f"❌ Admin creation error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error adding admin: {e}")
            return False
        finally:
            conn.close()
    
    def authenticate_admin(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate admin with username/password"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, password_hash, salt, full_name, fingerprint_slot
                FROM admins 
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            admin_data = dict(row)
            
            # Verify password
            if self.verify_password(password, admin_data['password_hash'], admin_data['salt']):
                # Update last login
                cursor.execute('''
                    UPDATE admins SET last_login = CURRENT_TIMESTAMP WHERE id = ?
                ''', (admin_data['id'],))
                conn.commit()
                
                # Remove sensitive data before returning
                del admin_data['password_hash']
                del admin_data['salt']
                
                return admin_data
            
            return None
            
        except Exception as e:
            print(f"❌ Admin authentication error: {e}")
            return None
        finally:
            conn.close()
    
    def get_admin_by_fingerprint(self, fingerprint_slot: int) -> Optional[Dict]:
        """Get admin by fingerprint slot"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, full_name, fingerprint_slot
                FROM admins 
                WHERE fingerprint_slot = ? AND is_active = 1
            ''', (fingerprint_slot,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            print(f"❌ Error fetching admin by fingerprint: {e}")
            return None
        finally:
            conn.close()
    
    # =================== TIME TRACKING OPERATIONS ===================
    
    def record_time_action(self, person_id: str, person_name: str, person_type: str, 
                          action: str, additional_info: str = None) -> bool:
        """Record time IN/OUT action"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Insert time record
            cursor.execute('''
                INSERT INTO time_records (person_id, person_name, person_type, action, additional_info)
                VALUES (?, ?, ?, ?, ?)
            ''', (person_id, person_name, person_type, action, additional_info))
            
            # Update current status
            cursor.execute('''
                INSERT OR REPLACE INTO current_status 
                (person_id, person_name, person_type, current_status, additional_info)
                VALUES (?, ?, ?, ?, ?)
            ''', (person_id, person_name, person_type, action, additional_info))
            
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
    
    # =================== ARCHIVE OPERATIONS ===================
    
    def archive_old_records(self, days_old: int = 90) -> int:
        """Archive old time records"""
        cutoff_date = (datetime.now() - timedelta(days=days_old)).date()
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Get old records
            cursor.execute('''
                SELECT * FROM time_records WHERE date < ?
            ''', (cutoff_date,))
            
            old_records = cursor.fetchall()
            archived_count = 0
            
            for record in old_records:
                # Archive the record
                record_data = dict(record)
                cursor.execute('''
                    INSERT INTO archived_records (original_table, original_id, data, archived_reason)
                    VALUES (?, ?, ?, ?)
                ''', ("time_records", record['id'], json.dumps(record_data, default=str), 
                     f"Auto-archived after {days_old} days"))
                
                # Delete original
                cursor.execute("DELETE FROM time_records WHERE id = ?", (record['id'],))
                archived_count += 1
            
            conn.commit()
            print(f"✅ Archived {archived_count} old records")
            return archived_count
            
        except Exception as e:
            print(f"❌ Error archiving records: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def get_archived_records(self, table_name: str = None, limit: int = 100) -> List[Dict]:
        """Get archived records"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            if table_name:
                cursor.execute('''
                    SELECT * FROM archived_records 
                    WHERE original_table = ?
                    ORDER BY archived_at DESC LIMIT ?
                ''', (table_name, limit))
            else:
                cursor.execute('''
                    SELECT * FROM archived_records 
                    ORDER BY archived_at DESC LIMIT ?
                ''', (limit,))
            
            records = []
            for row in cursor.fetchall():
                record = dict(row)
                try:
                    record['data'] = json.loads(record['data'])
                except:
                    pass
                records.append(record)
            
            return records
            
        except Exception as e:
            print(f"❌ Error getting archived records: {e}")
            return []
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
            
            report_data = {
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
            
            # Save report
            cursor.execute('''
                INSERT INTO reports (report_type, report_date, data, generated_by)
                VALUES (?, ?, ?, ?)
            ''', ("daily", target_date, json.dumps(report_data), "system"))
            
            conn.commit()
            return report_data
            
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
        """Clear all time records (with archive option)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Archive first
            self.archive_old_records(days_old=0)  # Archive all
            
            # Clear tables
            cursor.execute("DELETE FROM time_records")
            cursor.execute("DELETE FROM current_status")
            
            conn.commit()
            print("✅ All time records cleared (archived)")
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
            tables = ['students', 'admins', 'time_records', 'current_status', 'guests', 'archived_records', 'reports']
            
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
    
    def backup_database(self, backup_path: str = None) -> str:
        """Create database backup"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_motorpass_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return ""

# Create global instance
db = MotorPassDatabase()

# =================== COMPATIBILITY FUNCTIONS ===================
# These maintain compatibility with existing code

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

# Print initialization message
if __name__ == "__main__":
    print("🗄️ MotorPass Unified Database System")
    print(f"📊 Database: {DB_FILE}")
    stats = db.get_database_stats()
    print("📈 Statistics:", stats)
