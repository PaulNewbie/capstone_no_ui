# setup_motorpass_db.py - Simple setup script for motorpass.db

import sqlite3
import os
import json
from datetime import datetime

def setup_motorpass_database():
    """Setup the centralized motorpass.db database"""
    
    print("🚀 Setting up MotorPass Database")
    print("=" * 50)
    
    # Create database directory
    os.makedirs("database", exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect("database/motorpass.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    print("📋 Creating tables...")
    
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
    print("   ✅ Students table created")
    
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
    print("   ✅ Staff table created")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guests (
            guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            plate_number TEXT NOT NULL,
            office_visiting TEXT NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("   ✅ Guests table created")
    
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
    print("   ✅ Time tracking table created")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_status (
            user_id TEXT PRIMARY KEY,
            user_name TEXT NOT NULL,
            user_type TEXT NOT NULL CHECK(user_type IN ('STUDENT', 'STAFF', 'GUEST')),
            status TEXT NOT NULL CHECK(status IN ('IN', 'OUT')),
            last_action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("   ✅ Current status table created")
    
    # Create indexes
    print("\n🔍 Creating indexes...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_name ON students(full_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_staff_name ON staff(full_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_tracking_user ON time_tracking(user_id, user_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_tracking_date ON time_tracking(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_current_status_type ON current_status(user_type)')
    print("   ✅ Indexes created")
    
    conn.commit()
    
    # Check if we have any old data to import
    print("\n🔍 Checking for existing data...")
    
    imported_something = False
    
    # Import from old students.db if exists
    if os.path.exists("database/students.db"):
        print("   📁 Found old students.db, importing...")
        old_conn = sqlite3.connect("database/students.db")
        old_cursor = old_conn.cursor()
        
        try:
            old_cursor.execute("SELECT * FROM students")
            old_data = old_cursor.fetchall()
            
            student_count = 0
            staff_count = 0
            
            for row in old_data:
                # Parse the old data structure
                if len(row) >= 9:  # Make sure we have enough columns
                    full_name = row[0]
                    license_number = row[1]
                    expiration_date = row[2]
                    plate_number = row[3]
                    course = row[4]
                    student_id = row[5]
                    staff_role = row[6]
                    staff_no = row[7]
                    user_type = row[8]
                    
                    if user_type == 'STUDENT' and student_id:
                        cursor.execute('''
                            INSERT OR IGNORE INTO students 
                            (student_id, full_name, course, license_number, 
                             license_expiration, plate_number)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (student_id, full_name, course or '', 
                              license_number, expiration_date, plate_number))
                        student_count += 1
                        
                    elif user_type == 'STAFF' and staff_no:
                        cursor.execute('''
                            INSERT OR IGNORE INTO staff 
                            (staff_no, full_name, staff_role, license_number, 
                             license_expiration, plate_number)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (staff_no, full_name, staff_role or '', 
                              license_number, expiration_date, plate_number))
                        staff_count += 1
            
            print(f"   ✅ Imported {student_count} students and {staff_count} staff")
            imported_something = True
            
        except Exception as e:
            print(f"   ⚠️ Could not import from old database: {e}")
        
        old_conn.close()
    
    # Import fingerprint data if exists
    if os.path.exists("json_folder/fingerprint_database.json"):
        print("   📁 Found fingerprint database, importing...")
        try:
            with open("json_folder/fingerprint_database.json", 'r') as f:
                fingerprint_data = json.load(f)
            
            fp_count = 0
            for slot, data in fingerprint_data.items():
                if slot == "1":  # Skip admin
                    continue
                
                user_type = data.get('user_type', 'STUDENT')
                
                if user_type == 'STUDENT' and data.get('student_id'):
                    cursor.execute('''
                        UPDATE students SET fingerprint_slot = ? 
                        WHERE student_id = ?
                    ''', (int(slot), data['student_id']))
                    fp_count += 1
                    
                elif user_type == 'STAFF' and data.get('staff_no'):
                    cursor.execute('''
                        UPDATE staff SET fingerprint_slot = ? 
                        WHERE staff_no = ?
                    ''', (int(slot), data['staff_no']))
                    fp_count += 1
            
            print(f"   ✅ Imported {fp_count} fingerprint assignments")
            imported_something = True
            
        except Exception as e:
            print(f"   ⚠️ Could not import fingerprints: {e}")
    
    conn.commit()
    
    # Show database statistics
    print("\n📊 Database Statistics:")
    cursor.execute('SELECT COUNT(*) FROM students')
    print(f"   🎓 Students: {cursor.fetchone()[0]}")
    
    cursor.execute('SELECT COUNT(*) FROM staff')
    print(f"   👔 Staff: {cursor.fetchone()[0]}")
    
    cursor.execute('SELECT COUNT(*) FROM time_tracking')
    print(f"   ⏰ Time records: {cursor.fetchone()[0]}")
    
    conn.close()
    
    print("\n✅ MotorPass database setup complete!")
    print(f"📁 Database location: database/motorpass.db")
    
    if imported_something:
        print("\n💡 Imported data from existing files.")
        print("💡 You can now delete the old database files if everything works correctly.")

if __name__ == "__main__":
    setup_motorpass_database()
