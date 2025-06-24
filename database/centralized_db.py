# database/centralized_db.py - New centralized database structure for MotorPass

import sqlite3
import os
import time
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Union

# Single database file
MOTORPASS_DB = "database/motorpass.db"

# =================== DATABASE SCHEMA ===================

def create_database_schema():
    """Create all tables in the centralized database"""
    try:
        os.makedirs("database", exist_ok=True)
        conn = sqlite3.connect(MOTORPASS_DB)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        cursor = conn.cursor()
        
        # 1. Students table
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
        
        # 2. Staff table
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
        
        # 3. Guests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guests (
                guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                plate_number TEXT NOT NULL,
                office_visiting TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 4. Time tracking table (unified for all user types)
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
        
        # 5. Current status table (who's currently inside)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS current_status (
                user_id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                user_type TEXT NOT NULL CHECK(user_type IN ('STUDENT', 'STAFF', 'GUEST')),
                status TEXT NOT NULL CHECK(status IN ('IN', 'OUT')),
                last_action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_name ON students(full_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_staff_name ON staff(full_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_tracking_user ON time_tracking(user_id, user_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_tracking_date ON time_tracking(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_current_status_type ON current_status(user_type)')
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database creation error: {e}")
        return False

# =================== STUDENT OPERATIONS ===================

def add_student(student_data: Dict) -> bool:
    """Add or update a student record"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO students 
            (student_id, full_name, course, license_number, license_expiration, 
             plate_number, fingerprint_slot, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            student_data['student_id'],
            student_data['full_name'],
            student_data['course'],
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

def get_student(student_id: str) -> Optional[Dict]:
    """Get student by ID"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = ['student_id', 'full_name', 'course', 'license_number', 
                      'license_expiration', 'plate_number', 'fingerprint_slot', 
                      'enrolled_date', 'last_updated']
            return dict(zip(columns, row))
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching student: {e}")
        return None

def get_all_students() -> List[Dict]:
    """Get all students"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM students ORDER BY full_name')
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['student_id', 'full_name', 'course', 'license_number', 
                  'license_expiration', 'plate_number', 'fingerprint_slot', 
                  'enrolled_date', 'last_updated']
        
        return [dict(zip(columns, row)) for row in rows]
        
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
            (staff_no, full_name, staff_role, license_number, license_expiration, 
             plate_number, fingerprint_slot, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            staff_data['staff_no'],
            staff_data['full_name'],
            staff_data['staff_role'],
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

def get_staff(staff_no: str) -> Optional[Dict]:
    """Get staff by ID"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM staff WHERE staff_no = ?', (staff_no,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = ['staff_no', 'full_name', 'staff_role', 'license_number', 
                      'license_expiration', 'plate_number', 'fingerprint_slot', 
                      'enrolled_date', 'last_updated']
            return dict(zip(columns, row))
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching staff: {e}")
        return None

def get_all_staff() -> List[Dict]:
    """Get all staff members"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM staff ORDER BY full_name')
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['staff_no', 'full_name', 'staff_role', 'license_number', 
                  'license_expiration', 'plate_number', 'fingerprint_slot', 
                  'enrolled_date', 'last_updated']
        
        return [dict(zip(columns, row)) for row in rows]
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching staff: {e}")
        return []

# =================== GUEST OPERATIONS ===================

def add_guest(guest_data: Dict) -> int:
    """Add a guest record and return guest_id"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO guests (full_name, plate_number, office_visiting)
            VALUES (?, ?, ?)
        ''', (
            guest_data['full_name'],
            guest_data['plate_number'],
            guest_data['office_visiting']
        ))
        
        guest_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return guest_id
        
    except sqlite3.Error as e:
        print(f"❌ Error adding guest: {e}")
        return -1

def get_recent_guests(limit: int = 10) -> List[Dict]:
    """Get recent guest entries"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM guests 
            ORDER BY created_date DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['guest_id', 'full_name', 'plate_number', 'office_visiting', 'created_date']
        return [dict(zip(columns, row)) for row in rows]
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching guests: {e}")
        return []

# =================== UNIFIED USER LOOKUP ===================

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user info regardless of type (student or staff)"""
    # Try student first
    student = get_student(user_id)
    if student:
        return {
            **student,
            'user_type': 'STUDENT',
            'unified_id': student['student_id']
        }
    
    # Try staff
    staff = get_staff(user_id)
    if staff:
        return {
            **staff,
            'user_type': 'STAFF',
            'unified_id': staff['staff_no']
        }
    
    return None

def search_users(search_term: str) -> List[Dict]:
    """Search for users by name or ID across students and staff"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        results = []
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
        
        conn.close()
        return results
        
    except sqlite3.Error as e:
        print(f"❌ Error searching users: {e}")
        return []

# =================== TIME TRACKING OPERATIONS ===================

def record_time_action(user_id: str, user_name: str, user_type: str, action: str) -> bool:
    """Record a time IN or OUT action"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Record in time_tracking table
        cursor.execute('''
            INSERT INTO time_tracking (user_id, user_name, user_type, action, date, time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, user_name, user_type, action, current_date, current_time))
        
        # Update current_status table
        cursor.execute('''
            INSERT OR REPLACE INTO current_status (user_id, user_name, user_type, status)
            VALUES (?, ?, ?, ?)
        ''', (user_id, user_name, user_type, action))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error recording time action: {e}")
        return False

def get_user_current_status(user_id: str) -> Optional[str]:
    """Get current status (IN/OUT) for a user"""
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

def get_users_currently_inside() -> List[Dict]:
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
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'user_id': row[0],
            'user_name': row[1],
            'user_type': row[2],
            'time_in': row[3]
        } for row in rows]
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching users inside: {e}")
        return []

def get_time_records(date: Optional[str] = None, user_type: Optional[str] = None) -> List[Dict]:
    """Get time records with optional filters"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM time_tracking WHERE 1=1'
        params = []
        
        if date:
            query += ' AND date = ?'
            params.append(date)
        
        if user_type:
            query += ' AND user_type = ?'
            params.append(user_type)
        
        query += ' ORDER BY timestamp DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'user_id', 'user_name', 'user_type', 'action', 
                  'timestamp', 'date', 'time']
        
        return [dict(zip(columns, row)) for row in rows]
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching time records: {e}")
        return []

# =================== FINGERPRINT SLOT MANAGEMENT ===================

def assign_fingerprint_slot(user_id: str, user_type: str, slot: int) -> bool:
    """Assign a fingerprint slot to a user"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        if user_type == 'STUDENT':
            cursor.execute('''
                UPDATE students SET fingerprint_slot = ? WHERE student_id = ?
            ''', (slot, user_id))
        elif user_type == 'STAFF':
            cursor.execute('''
                UPDATE staff SET fingerprint_slot = ? WHERE staff_no = ?
            ''', (slot, user_id))
        else:
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error assigning fingerprint slot: {e}")
        return False

def get_user_by_fingerprint_slot(slot: int) -> Optional[Dict]:
    """Get user info by fingerprint slot"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        # Check students
        cursor.execute('SELECT * FROM students WHERE fingerprint_slot = ?', (slot,))
        student_row = cursor.fetchone()
        
        if student_row:
            columns = ['student_id', 'full_name', 'course', 'license_number', 
                      'license_expiration', 'plate_number', 'fingerprint_slot', 
                      'enrolled_date', 'last_updated']
            student_data = dict(zip(columns, student_row))
            conn.close()
            return {
                **student_data,
                'user_type': 'STUDENT',
                'unified_id': student_data['student_id']
            }
        
        # Check staff
        cursor.execute('SELECT * FROM staff WHERE fingerprint_slot = ?', (slot,))
        staff_row = cursor.fetchone()
        
        if staff_row:
            columns = ['staff_no', 'full_name', 'staff_role', 'license_number', 
                      'license_expiration', 'plate_number', 'fingerprint_slot', 
                      'enrolled_date', 'last_updated']
            staff_data = dict(zip(columns, staff_row))
            conn.close()
            return {
                **staff_data,
                'user_type': 'STAFF',
                'unified_id': staff_data['staff_no']
            }
        
        conn.close()
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching user by fingerprint: {e}")
        return None

def get_used_fingerprint_slots() -> List[int]:
    """Get list of all used fingerprint slots"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        used_slots = []
        
        # Get from students
        cursor.execute('SELECT fingerprint_slot FROM students WHERE fingerprint_slot IS NOT NULL')
        used_slots.extend([row[0] for row in cursor.fetchall()])
        
        # Get from staff
        cursor.execute('SELECT fingerprint_slot FROM staff WHERE fingerprint_slot IS NOT NULL')
        used_slots.extend([row[0] for row in cursor.fetchall()])
        
        conn.close()
        return sorted(used_slots)
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching used slots: {e}")
        return []

# =================== STATISTICS ===================

def get_database_statistics() -> Dict:
    """Get overall database statistics"""
    try:
        conn = sqlite3.connect(MOTORPASS_DB)
        cursor = conn.cursor()
        
        stats = {}
        
        # Count students
        cursor.execute('SELECT COUNT(*) FROM students')
        stats['total_students'] = cursor.fetchone()[0]
        
        # Count staff
        cursor.execute('SELECT COUNT(*) FROM staff')
        stats['total_staff'] = cursor.fetchone()[0]
        
        # Count guests
        cursor.execute('SELECT COUNT(*) FROM guests')
        stats['total_guests'] = cursor.fetchone()[0]
        
        # Count currently inside
        cursor.execute('SELECT COUNT(*) FROM current_status WHERE status = "IN"')
        stats['currently_inside'] = cursor.fetchone()[0]
        
        # Breakdown by type
        cursor.execute('''
            SELECT user_type, COUNT(*) FROM current_status 
            WHERE status = "IN" 
            GROUP BY user_type
        ''')
        
        inside_breakdown = {}
        for row in cursor.fetchall():
            inside_breakdown[row[0].lower() + 's_inside'] = row[1]
        stats.update(inside_breakdown)
        
        # Today's activity
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM time_tracking WHERE date = ?', (today,))
        stats['todays_activity'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
        
    except sqlite3.Error as e:
        print(f"❌ Error getting statistics: {e}")
        return {}

# =================== DATA IMPORT/SYNC ===================

def sync_from_google_sheets(sheet_data: List[Dict]) -> Dict[str, int]:
    """Sync data from Google Sheets"""
    results = {'students_added': 0, 'staff_added': 0, 'errors': 0}
    
    try:
        for row in sheet_data:
            try:
                # Extract common fields
                full_name = row.get('Full Name', '').strip()
                license_number = row.get('License Number', '').strip()
                expiration_date = row.get('License Expiration Date', '').strip()
                plate_number = row.get('Plate Number of the Motorcycle', '').strip()
                
                # Check if it's a student or staff
                student_id = row.get('Student No.', '').strip()
                staff_no = row.get('Staff No.', '').strip()
                
                if not full_name:
                    continue
                
                if student_id and not staff_no:
                    # It's a student
                    student_data = {
                        'student_id': student_id,
                        'full_name': full_name,
                        'course': row.get('Course', '').strip(),
                        'license_number': license_number,
                        'license_expiration': expiration_date,
                        'plate_number': plate_number
                    }
                    
                    if add_student(student_data):
                        results['students_added'] += 1
                    else:
                        results['errors'] += 1
                        
                elif staff_no and not student_id:
                    # It's a staff member
                    staff_data = {
                        'staff_no': staff_no,
                        'full_name': full_name,
                        'staff_role': row.get('Staff Role', '').strip(),
                        'license_number': license_number,
                        'license_expiration': expiration_date,
                        'plate_number': plate_number
                    }
                    
                    if add_staff(staff_data):
                        results['staff_added'] += 1
                    else:
                        results['errors'] += 1
                        
                elif student_id and staff_no:
                    # Both filled - skip with warning
                    print(f"⚠️ Both Student No. and Staff No. filled for {full_name}")
                    results['errors'] += 1
                    
            except Exception as e:
                print(f"❌ Error processing row: {e}")
                results['errors'] += 1
                
        return results
        
    except Exception as e:
        print(f"❌ Sync error: {e}")
        results['errors'] += -1
        return results

# =================== MAINTENANCE ===================

def clear_time_records() -> bool:
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

def backup_database(backup_path: Optional[str] = None) -> bool:
    """Create a backup of the database"""
    try:
        import shutil
        from datetime import datetime
        
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"database/backups/motorpass_backup_{timestamp}.db"
        
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(MOTORPASS_DB, backup_path)
        
        print(f"✅ Database backed up to: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Backup error: {e}")
        return False

# =================== INITIALIZATION ===================

def initialize_database():
    """Initialize the centralized database"""
    print("🗄️ Initializing MotorPass centralized database...")
    
    if create_database_schema():
        print("✅ Database schema created successfully")
        
        stats = get_database_statistics()
        print(f"📊 Database Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        return True
    else:
        print("❌ Failed to create database schema")
        return False

# =================== MIGRATION HELPER ===================

def migrate_from_old_structure():
    """Migrate data from old database structure to new centralized database"""
    print("🔄 Starting migration from old database structure...")
    
    try:
        # First ensure new database exists
        if not initialize_database():
            return False
        
        migrated_count = 0
        
        # Migrate from old students.db if it exists
        old_student_db = "database/students.db"
        if os.path.exists(old_student_db):
            print("📋 Found old students.db, migrating...")
            
            old_conn = sqlite3.connect(old_student_db)
            cursor = old_conn.cursor()
            
            cursor.execute('SELECT * FROM students')
            old_records = cursor.fetchall()
            
            for record in old_records:
                # Map old structure to new
                if record[8] == 'STUDENT':  # user_type field
                    student_data = {
                        'student_id': record[5],  # student_id
                        'full_name': record[0],   # full_name
                        'course': record[4],      # course
                        'license_number': record[1],
                        'license_expiration': record[2],
                        'plate_number': record[3]
                    }
                    if add_student(student_data):
                        migrated_count += 1
                        
                elif record[8] == 'STAFF':
                    staff_data = {
                        'staff_no': record[7],    # staff_no
                        'full_name': record[0],   # full_name
                        'staff_role': record[6],  # staff_role
                        'license_number': record[1],
                        'license_expiration': record[2],
                        'plate_number': record[3]
                    }
                    if add_staff(staff_data):
                        migrated_count += 1
            
            old_conn.close()
            print(f"✅ Migrated {migrated_count} records from old database")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

if __name__ == "__main__":
    # Test the new database structure
    print("🚀 Testing centralized database...")
    
    if initialize_database():
        print("\n✅ Database initialized successfully!")
        
        # Test adding a student
        test_student = {
            'student_id': '2021-00123',
            'full_name': 'Juan Dela Cruz',
            'course': 'BSIT',
            'license_number': 'N01-23-456789',
            'license_expiration': '2025-12-31',
            'plate_number': 'ABC 123'
        }
        
        if add_student(test_student):
            print("✅ Test student added")
            
        # Test lookup
        user = get_user_by_id('2021-00123')
        if user:
            print(f"✅ Found user: {user['full_name']} ({user['user_type']})")
